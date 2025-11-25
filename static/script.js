let stream = null;
let modalStream = null;
let capturedImage = null;
let currentCameraId = null;

// Initialize on page load
window.addEventListener('DOMContentLoaded', () => {
    console.log('Page loaded, initializing...');
    
    // Update time immediately and then every second
    updateCurrentTime();
    setInterval(updateCurrentTime, 1000);
    
    // Load initial data
    loadOngoingAttendance();
    loadCompletedAttendance();
    loadActiveSessions();
    checkActiveCameras();
    loadAlerts();
    loadClassTimeSettings();
    
    // Auto-start MacBook camera if no cameras are active
    setTimeout(() => {
        autoStartDefaultCamera();
    }, 2000); // Wait 2 seconds for page to fully load
    
    // Auto-refresh ongoing attendance every 5 seconds
    setInterval(loadOngoingAttendance, 5000);
    // Auto-refresh completed attendance every 10 seconds
    setInterval(loadCompletedAttendance, 10000);
    // Auto-refresh active sessions every 5 seconds
    setInterval(loadActiveSessions, 5000);
    // Auto-refresh alerts every 3 seconds
    setInterval(loadAlerts, 3000);
    
    // Setup forms
    setupCameraForm();
    setupUserForm();
    
    console.log('Initialization complete');
});

// Update current time display
function updateCurrentTime() {
    try {
        const now = new Date();
        const timeString = now.toLocaleString('en-US', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: false
        });
        const timeDisplay = document.getElementById('time-display');
        if (timeDisplay) {
            timeDisplay.textContent = timeString;
        } else {
            console.warn('Time display element not found');
        }
    } catch (error) {
        console.error('Error updating time:', error);
    }
}

// Modal Functions
function openAddUserModal() {
    const modal = document.getElementById('add-user-modal');
    if (modal) {
        modal.style.display = 'block';
        startModalCamera();
    } else {
        console.error('Add user modal not found');
    }
}

function closeAddUserModal() {
    const modal = document.getElementById('add-user-modal');
    if (modal) {
        modal.style.display = 'none';
        stopModalCamera();
        const form = document.getElementById('user-form');
        if (form) form.reset();
        retakePhoto();
    }
}

function openManageUsersModal() {
    const modal = document.getElementById('manage-users-modal');
    if (modal) {
        modal.style.display = 'block';
        loadUsers();
    } else {
        console.error('Manage users modal not found');
    }
}

function closeManageUsersModal() {
    const modal = document.getElementById('manage-users-modal');
    if (modal) modal.style.display = 'none';
}

function openCameraModal() {
    const modal = document.getElementById('camera-modal');
    if (modal) {
        modal.style.display = 'block';
        checkActiveCameras();
        
        // Pre-fill with default MacBook camera settings
        const cameraIdInput = document.getElementById('camera-id');
        const cameraUrlInput = document.getElementById('camera-url');
        if (cameraIdInput && !cameraIdInput.value) {
            cameraIdInput.value = 'macbook_camera';
        }
        if (cameraUrlInput && !cameraUrlInput.value) {
            cameraUrlInput.value = '0';
        }
    } else {
        console.error('Camera modal not found');
    }
}

function closeCameraModal() {
    const modal = document.getElementById('camera-modal');
    if (modal) {
        modal.style.display = 'none';
        const form = document.getElementById('camera-form');
        if (form) {
            form.reset();
            const cameraIdInput = document.getElementById('camera-id');
            const urlInput = document.getElementById('camera-url');
            if (cameraIdInput) cameraIdInput.value = 'macbook_camera';
            if (urlInput) urlInput.value = '0';
        }
    }
}

// Close modals when clicking outside
window.onclick = function (event) {
    const modals = ['add-user-modal', 'manage-users-modal', 'camera-modal', 'settings-modal', 'analytics-modal', 'approvals-modal'];
    modals.forEach(modalId => {
        const modal = document.getElementById(modalId);
        if (event.target === modal) {
            if (modalId === 'add-user-modal') closeAddUserModal();
            else if (modalId === 'manage-users-modal') closeManageUsersModal();
            else if (modalId === 'camera-modal') closeCameraModal();
            else if (modalId === 'settings-modal') closeSettingsModal();
            else if (modalId === 'analytics-modal') closeAnalyticsModal();
            else if (modalId === 'approvals-modal') closeApprovalsModal();
        }
    });
}

// Modal Camera Functions (for Add User)
async function startModalCamera() {
    try {
        if (modalStream) {
            stopModalCamera();
        }

        modalStream = await navigator.mediaDevices.getUserMedia({
            video: {
                width: { ideal: 640 },
                height: { ideal: 480 },
                facingMode: 'user'
            }
        });
        const video = document.getElementById('video');
        const captureBtn = document.getElementById('capture-btn');
        const cameraStatus = document.getElementById('modal-camera-status');

        if (video) {
            video.srcObject = modalStream;
            video.onloadedmetadata = () => {
                video.play().then(() => {
                    console.log('Modal camera ready');
                    if (captureBtn) captureBtn.disabled = false;
                    if (cameraStatus) cameraStatus.style.display = 'block';
                }).catch(err => {
                    console.error('Error playing video:', err);
                });
            };
        }
    } catch (error) {
        console.error('Error accessing camera:', error);
        showMessage('user-message', 'Error accessing camera. Please allow camera permissions.', 'error');
    }
}

function stopModalCamera() {
    if (modalStream) {
        modalStream.getTracks().forEach(track => track.stop());
        modalStream = null;
    }
    const video = document.getElementById('video');
    if (video) {
        video.srcObject = null;
    }
}

function captureImage() {
    const video = document.getElementById('video');
    const canvas = document.getElementById('canvas');
    const preview = document.getElementById('preview');
    const previewContainer = document.getElementById('preview-container');
    const captureBtn = document.getElementById('capture-btn');
    const retakeBtn = document.getElementById('retake-btn');

    if (!video || !video.videoWidth || !video.videoHeight) {
        showMessage('user-message', 'Camera not ready. Please wait a moment and try again.', 'error');
        return;
    }

    if (video.readyState !== video.HAVE_ENOUGH_DATA) {
        showMessage('user-message', 'Video stream not ready. Please wait a moment.', 'error');
        return;
    }

    try {
        if (!canvas) {
            showMessage('user-message', 'Canvas element not found', 'error');
            return;
        }

        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;

        const ctx = canvas.getContext('2d');
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

        capturedImage = canvas.toDataURL('image/jpeg', 0.95);
        if (preview) preview.src = capturedImage;

        if (previewContainer) previewContainer.style.display = 'block';
        if (captureBtn) captureBtn.style.display = 'none';
        if (retakeBtn) retakeBtn.style.display = 'inline-block';

        const messageDiv = document.getElementById('user-message');
        if (messageDiv) messageDiv.style.display = 'none';
    } catch (error) {
        console.error('Error capturing image:', error);
        showMessage('user-message', 'Error capturing image. Please try again.', 'error');
    }
}

function retakePhoto() {
    const previewContainer = document.getElementById('preview-container');
    const captureBtn = document.getElementById('capture-btn');
    const retakeBtn = document.getElementById('retake-btn');

    if (previewContainer) previewContainer.style.display = 'none';
    if (captureBtn) {
        captureBtn.style.display = 'inline-block';
        captureBtn.disabled = false;
    }
    if (retakeBtn) retakeBtn.style.display = 'none';
    capturedImage = null;
}

// Setup User Form
function setupUserForm() {
    const userForm = document.getElementById('user-form');
    if (userForm) {
        userForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            if (!capturedImage) {
                showMessage('user-message', 'Please capture an image first', 'error');
                return;
            }

            const nameInput = document.getElementById('user-name');
            const usnInput = document.getElementById('user-usn');
            
            if (!nameInput || !usnInput) {
                showMessage('user-message', 'Form fields not found', 'error');
                return;
            }

            const name = nameInput.value.trim();
            const usn = usnInput.value.trim().toUpperCase();

            if (!name || !usn) {
                showMessage('user-message', 'Please fill in all fields', 'error');
                return;
            }

            try {
                // Show loading state
                const submitBtn = userForm.querySelector('button[type="submit"]');
                const originalBtnText = submitBtn ? submitBtn.textContent : '';
                if (submitBtn) {
                    submitBtn.disabled = true;
                    submitBtn.textContent = 'Adding User...';
                }

                const blob = await (await fetch(capturedImage)).blob();
                const formData = new FormData();
                formData.append('name', name);
                formData.append('usn', usn);
                formData.append('image', blob, 'captured_image.jpg');

                const res = await fetch('/api/users', {
                    method: 'POST',
                    body: formData
                });

                // Parse response
                let data;
                try {
                    const text = await res.text();
                    if (!text) {
                        throw new Error('Empty response from server');
                    }
                    data = JSON.parse(text);
                } catch (parseError) {
                    console.error('Failed to parse response:', parseError);
                    showMessage('user-message', `Server error: ${res.status} ${res.statusText}. Please check backend logs.`, 'error');
                    if (submitBtn) {
                        submitBtn.disabled = false;
                        submitBtn.textContent = originalBtnText;
                    }
                    return;
                }

                if (res.ok) {
                    showMessage('user-message', `User "${data.name}" (${data.usn}) added successfully!`, 'success');
                    userForm.reset();
                    retakePhoto();
                    
                    // Refresh users list if manage modal is open
                    const manageModal = document.getElementById('manage-users-modal');
                    if (manageModal && manageModal.style.display === 'block') {
                        setTimeout(() => loadUsers(), 500);
                    }
                    
                    // Refresh attendance
                    setTimeout(() => {
                        loadOngoingAttendance();
                        loadCompletedAttendance();
                    }, 1000);
                    
                    // Close modal after delay
                    setTimeout(() => {
                        closeAddUserModal();
                    }, 2000);
                } else {
                    showMessage('user-message', data.error || `Error: ${res.status} ${res.statusText}`, 'error');
                }
                
                // Restore button
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.textContent = originalBtnText;
                }
            } catch (error) {
                console.error('Error adding user:', error);
                let errorMsg = 'Error connecting to server';
                
                if (error.message.includes('fetch')) {
                    errorMsg = 'Cannot connect to server. Make sure backend is running on port 5001.';
                } else if (error.message.includes('blob')) {
                    errorMsg = 'Error processing image. Please capture the image again.';
                } else {
                    errorMsg = `Error: ${error.message}`;
                }
                
                showMessage('user-message', errorMsg, 'error');
                
                // Restore button
                const submitBtn = userForm.querySelector('button[type="submit"]');
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.textContent = 'Add User';
                }
            }
        });
        console.log('User form setup complete');
    } else {
        console.warn('User form not found');
    }
}

// Load Ongoing Attendance (People currently inside - no exit time)
async function loadOngoingAttendance() {
    const tbody = document.getElementById('ongoing-body');
    if (!tbody) {
        console.warn('Ongoing attendance body not found');
        return;
    }

    try {
        const response = await fetch('/api/attendance');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();

        // Filter for ongoing records (no exit time)
        const ongoingRecords = data.filter(record => !record.exit || record.exit === 'N/A' || record.exit === 'In Progress');

        tbody.innerHTML = '';

        if (ongoingRecords.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; padding: 20px; color: #666;">No ongoing attendance</td></tr>';
            return;
        }

        ongoingRecords.forEach(record => {
            const row = document.createElement('tr');
            row.classList.add('in-progress');

            // Calculate current duration
            const entryTime = new Date(record.entry);
            const now = new Date();
            const diffMinutes = Math.floor((now - entryTime) / 60000);
            const duration = diffMinutes < 60 ? `${diffMinutes} min` : `${Math.floor(diffMinutes / 60)}h ${diffMinutes % 60}m`;
            
            const isLate = record.is_late ? 1 : 0;
            const durationBadge = isLate ? 
                `<span class="duration-badge late-badge">${duration} (Late)</span>` : 
                `<span class="duration-badge">${duration}</span>`;

            row.innerHTML = `
                <td><strong>${record.name}</strong></td>
                <td><code style="background: #f0f0f0; padding: 4px 8px; border-radius: 4px;">${record.usn || 'N/A'}</code></td>
                <td>${record.entry}</td>
                <td>${durationBadge}</td>
                <td>🟢 Active</td>
            `;
            tbody.appendChild(row);
        });
    } catch (error) {
        console.error('Error loading ongoing attendance:', error);
        tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; padding: 20px; color: #dc3545;">Error loading data</td></tr>';
    }
}

// Load Completed Attendance (People who have exited)
async function loadCompletedAttendance() {
    const tbody = document.getElementById('completed-body');
    if (!tbody) {
        console.warn('Completed attendance body not found');
        return;
    }

    try {
        const response = await fetch('/api/attendance');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();

        // Filter for completed records (has exit time)
        const completedRecords = data.filter(record => record.exit && record.exit !== 'N/A' && record.exit !== 'In Progress');

        tbody.innerHTML = '';

        if (completedRecords.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 20px; color: #666;">No completed attendance records yet</td></tr>';
            return;
        }

        completedRecords.forEach(record => {
            const row = document.createElement('tr');

            const duration = record.duration || 'N/A';
            const isLate = record.is_late ? 1 : 0;
            const durationBadge = isLate ? 
                `<span class="duration-badge late-badge">${duration} (Late)</span>` : 
                `<span class="duration-badge">${duration}</span>`;

            row.innerHTML = `
                <td>${record.id}</td>
                <td><strong>${record.name}</strong></td>
                <td><code style="background: #f0f0f0; padding: 4px 8px; border-radius: 4px;">${record.usn || 'N/A'}</code></td>
                <td>${record.entry}</td>
                <td>${record.exit}</td>
                <td>${durationBadge}</td>
                <td>✅ Completed</td>
            `;
            tbody.appendChild(row);
        });
    } catch (error) {
        console.error('Error loading completed attendance:', error);
        tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 20px; color: #dc3545;">Error loading data</td></tr>';
    }
}

// Legacy function for backward compatibility
async function loadAttendance(showLoading = false) {
    await loadCompletedAttendance();
}

async function loadActiveSessions() {
    try {
        const response = await fetch('/api/students/inside');
        if (!response.ok) return;
        const data = await response.json();

        const cameraStatus = document.getElementById('camera-status');
        if (data.length > 0 && cameraStatus) {
            cameraStatus.style.display = 'block';
            cameraStatus.textContent = `Active: ${data.length} person(s) detected`;
        }
    } catch (error) {
        console.error('Error loading active sessions:', error);
    }
}

// Camera Setup Form
function setupCameraForm() {
    const cameraForm = document.getElementById('camera-form');
    if (cameraForm) {
        cameraForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const cameraIdInput = document.getElementById('camera-id');
            const cameraUrlInput = document.getElementById('camera-url');
            
            if (!cameraIdInput || !cameraUrlInput) {
                showMessage('camera-message', 'Form fields not found', 'error');
                return;
            }

            const cameraId = cameraIdInput.value.trim();
            const cameraUrl = cameraUrlInput.value.trim();

            if (!cameraId) {
                showMessage('camera-message', 'Please enter a Camera ID', 'error');
                return;
            }

            const url = cameraUrl === '' || isNaN(cameraUrl) ? cameraUrl : parseInt(cameraUrl);

            try {
                const response = await fetch('/api/cameras', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        camera_id: cameraId,
                        camera_url: url
                    })
                });

                const data = await response.json();

                if (response.ok) {
                    const knownFaces = data.known_faces_count || 0;
                    showMessage('camera-message', `Camera "${cameraId}" started! (${knownFaces} registered faces)`, 'success');

                    startLiveVideoFeed(cameraId);
                    
                    cameraForm.reset();
                    cameraUrlInput.value = '0';

                    const activeCameras = document.getElementById('active-cameras');
                    if (activeCameras) {
                        if (!activeCameras.querySelector('h3')) {
                            activeCameras.innerHTML = '<h3>Active Cameras:</h3><ul id="camera-list"></ul>';
                        }
                        const list = document.getElementById('camera-list');
                        if (list) {
                            const li = document.createElement('li');
                            li.textContent = `${cameraId} - Running`;
                            list.appendChild(li);
                        }
                    }

                    setTimeout(() => {
                        const msgDiv = document.getElementById('camera-message');
                        if (msgDiv) msgDiv.style.display = 'none';
                    }, 3000);

                    setTimeout(() => {
                        closeCameraModal();
                    }, 2000);
                } else {
                    showMessage('camera-message', data.error || 'Error starting camera', 'error');
                }
            } catch (error) {
                showMessage('camera-message', 'Error connecting to server', 'error');
                console.error('Error:', error);
            }
        });
        console.log('Camera form setup complete');
    } else {
        console.warn('Camera form not found');
    }
}

// Start live video feed (connect to server stream)
function startLiveVideoFeed(cameraId) {
    currentCameraId = cameraId;
    const liveVideo = document.getElementById('live-video');
    const noCamera = document.getElementById('no-camera');
    
    if (liveVideo) {
        liveVideo.src = `/api/video_feed/${cameraId}`;
        liveVideo.classList.add('active');
        liveVideo.style.display = 'block';
        liveVideo.onerror = function() {
            console.error('Error loading video feed');
            if (noCamera) noCamera.style.display = 'block';
            if (liveVideo) liveVideo.style.display = 'none';
        };
    }
    if (noCamera) {
        noCamera.style.display = 'none';
    }
}

async function checkActiveCameras() {
    try {
        const response = await fetch('/api/cameras');
        if (!response.ok) {
            console.warn('Could not fetch cameras:', response.status);
            return [];
        }
        const data = await response.json();
        const activeCameras = document.getElementById('active-cameras');
        if (activeCameras) {
            if (data.length > 0) {
                activeCameras.innerHTML = '<h3>Active Cameras:</h3><ul id="camera-list"></ul>';
                const list = document.getElementById('camera-list');
                if (list) {
                    data.forEach(cam => {
                        const li = document.createElement('li');
                        li.textContent = `${cam.camera_id} - Running (Started: ${cam.started_at})`;
                        list.appendChild(li);
                    });
                }
                
                // If there's an active camera, start the video feed for the first one
                if (data.length > 0 && !currentCameraId) {
                    startLiveVideoFeed(data[0].camera_id);
                }
            } else {
                activeCameras.innerHTML = '<p style="color: #666; padding: 10px;">No active cameras</p>';
            }
        }
        return data; // Return cameras list for auto-start check
    } catch (err) {
        console.error('Error checking cameras:', err);
        return [];
    }
}

// Auto-start default MacBook camera if no cameras are active
async function autoStartDefaultCamera() {
    try {
        const cameras = await checkActiveCameras();
        if (!cameras || cameras.length === 0) {
            console.log('No cameras active, auto-starting MacBook camera...');
            const response = await fetch('/api/cameras', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    camera_id: 'macbook_camera',
                    camera_url: 0
                })
            });
            
            const data = await response.json();
            if (response.ok) {
                console.log('✅ MacBook camera started automatically');
                startLiveVideoFeed('macbook_camera');
                // Refresh camera list
                setTimeout(() => checkActiveCameras(), 1000);
            } else {
                console.warn('Could not auto-start camera:', data.error);
            }
        } else {
            console.log('Camera already active, skipping auto-start');
        }
    } catch (err) {
        console.error('Error auto-starting camera:', err);
    }
}

// Auto-start default MacBook camera if no cameras are active
async function autoStartDefaultCamera() {
    try {
        const cameras = await checkActiveCameras();
        if (!cameras || cameras.length === 0) {
            console.log('No cameras active, auto-starting MacBook camera...');
            const response = await fetch('/api/cameras', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    camera_id: 'macbook_camera',
                    camera_url: 0
                })
            });
            
            const data = await response.json();
            if (response.ok) {
                console.log('✅ MacBook camera started automatically');
                startLiveVideoFeed('macbook_camera');
                // Refresh camera list
                setTimeout(() => checkActiveCameras(), 1000);
            } else {
                console.warn('Could not auto-start camera:', data.error);
            }
        } else {
            console.log('Camera already active, skipping auto-start');
        }
    } catch (err) {
        console.error('Error auto-starting camera:', err);
    }
}

function showMessage(elementId, message, type) {
    const messageDiv = document.getElementById(elementId);
    if (messageDiv) {
        messageDiv.textContent = message;
        messageDiv.className = `message ${type}`;
        messageDiv.style.display = 'block';
    } else {
        console.warn(`Message element ${elementId} not found`);
    }
}

// Load and display users
async function loadUsers() {
    const loading = document.getElementById('users-loading');
    const container = document.getElementById('users-list-container');
    const tbody = document.getElementById('users-body');

    if (!loading || !container || !tbody) {
        console.error('Users table elements not found');
        return;
    }

    loading.style.display = 'block';
    container.style.display = 'none';

    try {
        const response = await fetch('/api/users');
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const users = await response.json();

        loading.style.display = 'none';
        container.style.display = 'block';

        if (users.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; padding: 20px;">No users registered yet</td></tr>';
            return;
        }

        tbody.innerHTML = users.map(user => `
            <tr>
                <td>${user.id}</td>
                <td><strong>${user.name}</strong></td>
                <td><code>${user.usn}</code></td>
                <td>${user.created_at || 'N/A'}</td>
                <td>
                    <button onclick="deleteUser(${user.id})" class="delete-btn">🗑️ Delete</button>
                </td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Error loading users:', error);
        loading.textContent = 'Error loading users';
    }
}

async function deleteUser(userId) {
    if (!confirm(`Are you sure you want to delete user ID ${userId}?`)) return;

    try {
        const response = await fetch(`/api/users/${userId}`, {
            method: 'DELETE'
        });

        const data = await response.json();

        if (response.ok) {
            alert('User deleted successfully');
            loadUsers();
            loadOngoingAttendance();
            loadCompletedAttendance();
        } else {
            alert(data.error || 'Error deleting user');
        }
    } catch (error) {
        console.error('Error deleting user:', error);
        alert('Error connecting to server');
    }
}

// Logout function
async function logout() {
    if (!confirm('Are you sure you want to logout?')) {
        return;
    }

    try {
        const response = await fetch('/logout', {
            method: 'POST'
        });

        const data = await response.json();

        if (response.ok && data.success) {
            window.location.href = '/login';
        } else {
            alert('Error logging out');
        }
    } catch (error) {
        console.error('Error logging out:', error);
        window.location.href = '/login';
    }
}

// Real-Time Alerts
function toggleNotifications() {
    const dropdown = document.getElementById('notification-dropdown');
    if (dropdown) {
        dropdown.classList.toggle('active');
    }
}

document.addEventListener('click', function(event) {
    const bell = document.querySelector('.notification-bell');
    const dropdown = document.getElementById('notification-dropdown');
    if (bell && dropdown && !bell.contains(event.target)) {
        dropdown.classList.remove('active');
    }
});

async function loadAlerts() {
    try {
        const response = await fetch('/api/alerts');
        if (!response.ok) return;
        const alerts = await response.json();
        
        const container = document.getElementById('alerts-container');
        const badge = document.getElementById('alert-badge');
        if (!container) return;
        
        if (badge) {
            if (alerts.length > 0) {
                badge.textContent = alerts.length > 99 ? '99+' : alerts.length;
                badge.style.display = 'flex';
            } else {
                badge.style.display = 'none';
            }
        }
        
        if (alerts.length === 0) {
            container.innerHTML = '<div class="no-alerts">No alerts yet</div>';
            return;
        }
        
        container.innerHTML = alerts.slice(-10).reverse().map(alert => {
            const icon = alert.type === 'late' ? '⚠️' : alert.type === 'entry' ? '✅' : '🚪';
            return `<div class="alert-item alert-${alert.type}">
                <span class="alert-icon">${icon}</span>
                <div class="alert-content">
                    <div class="alert-message">${alert.message}</div>
                    <div class="alert-time">${alert.timestamp}</div>
                </div>
            </div>`;
        }).join('');
    } catch (error) {
        console.error('Error loading alerts:', error);
    }
}

async function clearAlerts() {
    try {
        await fetch('/api/alerts/clear', { method: 'POST' });
        loadAlerts();
        const badge = document.getElementById('alert-badge');
        if (badge) badge.style.display = 'none';
    } catch (error) {
        console.error('Error clearing alerts:', error);
    }
}

// Approvals Modal
function openApprovalsModal() {
    const modal = document.getElementById('approvals-modal');
    if (modal) {
        modal.style.display = 'block';
        loadPendingApprovals();
    }
}

function closeApprovalsModal() {
    const modal = document.getElementById('approvals-modal');
    if (modal) modal.style.display = 'none';
}

async function loadPendingApprovals() {
    const loading = document.getElementById('approvals-loading');
    const container = document.getElementById('approvals-list-container');
    const tbody = document.getElementById('approvals-body');
    
    if (!loading || !container || !tbody) return;
    
    loading.style.display = 'block';
    container.style.display = 'none';
    
    try {
        const response = await fetch('/api/admin/approvals');
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const pending = await response.json();
        
        loading.style.display = 'none';
        
        if (pending.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 20px;">No pending approvals</td></tr>';
            container.style.display = 'block';
            return;
        }
        
        tbody.innerHTML = pending.map(user => `
            <tr>
                <td>${user.id}</td>
                <td><strong>${user.name}</strong></td>
                <td><code>${user.usn}</code></td>
                <td>${user.created_at}</td>
                <td>${user.image_paths ? user.image_paths.length : 0} photos</td>
                <td>
                    <button onclick="approveStudent(${user.id})" class="btn-approve">✅ Approve</button>
                    <button onclick="rejectStudent(${user.id})" class="btn-reject">❌ Reject</button>
                </td>
            </tr>
        `).join('');
        
        container.style.display = 'block';
    } catch (error) {
        console.error('Error loading approvals:', error);
        loading.textContent = 'Error loading approvals';
    }
}

async function approveStudent(userId) {
    if (!confirm('Approve this student registration?')) return;
    
    try {
        const response = await fetch(`/api/admin/approve/${userId}`, { method: 'POST' });
        const data = await response.json();
        
        if (response.ok) {
            alert('Student approved successfully');
            loadPendingApprovals();
            loadUsers();
        } else {
            alert(data.error || 'Error approving student');
        }
    } catch (error) {
        alert('Error approving student');
        console.error('Error:', error);
    }
}

async function rejectStudent(userId) {
    if (!confirm('Reject this student registration? This cannot be undone.')) return;
    
    try {
        const response = await fetch(`/api/admin/reject/${userId}`, { method: 'POST' });
        const data = await response.json();
        
        if (response.ok) {
            alert('Student rejected');
            loadPendingApprovals();
        } else {
            alert(data.error || 'Error rejecting student');
        }
    } catch (error) {
        alert('Error rejecting student');
        console.error('Error:', error);
    }
}

// Analytics Modal
function openAnalyticsModal() {
    const modal = document.getElementById('analytics-modal');
    const dateInput = document.getElementById('analytics-date');
    if (modal) {
        if (dateInput && !dateInput.value) {
            dateInput.value = new Date().toISOString().split('T')[0];
        }
        modal.style.display = 'block';
        loadAnalytics();
    }
}

function closeAnalyticsModal() {
    const modal = document.getElementById('analytics-modal');
    if (modal) modal.style.display = 'none';
}

async function loadAnalytics() {
    const dateInput = document.getElementById('analytics-date');
    const date = dateInput ? (dateInput.value || new Date().toISOString().split('T')[0]) : new Date().toISOString().split('T')[0];
    
    try {
        const response = await fetch(`/api/analytics?date=${date}`);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const data = await response.json();
        
        const elements = {
            'total-students': data.total_students || 0,
            'present-today': data.present_today || 0,
            'attendance-percent': `${data.attendance_percent || 0}%`,
            'late-count': data.late_count || 0,
            'avg-duration': `${data.avg_duration_minutes || 0} min`,
            'currently-inside': data.currently_inside || 0
        };
        
        Object.keys(elements).forEach(id => {
            const el = document.getElementById(id);
            if (el) el.textContent = elements[id];
        });
    } catch (error) {
        console.error('Error loading analytics:', error);
    }
}

// Settings Modal Functions
function openSettingsModal() {
    const modal = document.getElementById('settings-modal');
    if (modal) {
        modal.style.display = 'block';
        loadClassTimeSettings();
    }
}

function closeSettingsModal() {
    const modal = document.getElementById('settings-modal');
    if (modal) modal.style.display = 'none';
}

async function loadClassTimeSettings() {
    try {
        const response = await fetch('/api/class-time');
        if (!response.ok) return;
        const data = await response.json();
        
        if (data.class_start_time) {
            const timeParts = data.class_start_time.split(':');
            const timeValue = `${timeParts[0]}:${timeParts[1]}`;
            const timeInput = document.getElementById('settings-class-start-time');
            if (timeInput) timeInput.value = timeValue;
        }
        
        if (data.late_threshold_minutes !== undefined) {
            const thresholdInput = document.getElementById('settings-late-threshold');
            if (thresholdInput) thresholdInput.value = data.late_threshold_minutes;
        }
        
        if (data.last_updated) {
            const lastUpdatedText = document.getElementById('last-updated-text');
            if (lastUpdatedText) lastUpdatedText.textContent = data.last_updated;
        }
    } catch (error) {
        console.error('Error loading class time settings:', error);
    }
}

document.getElementById('settings-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const timeInput = document.getElementById('settings-class-start-time');
    const thresholdInput = document.getElementById('settings-late-threshold');
    
    if (!timeInput || !thresholdInput) {
        showMessage('settings-message', 'Form fields not found', 'error');
        return;
    }
    
    const classStartTime = timeInput.value;
    const lateThreshold = parseInt(thresholdInput.value);
    
    if (!classStartTime || isNaN(lateThreshold) || lateThreshold < 0) {
        showMessage('settings-message', 'Please fill all fields with valid values', 'error');
        return;
    }
    
    const timeValue = `${classStartTime}:00`;
    
    try {
        const response = await fetch('/api/class-time', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                class_start_time: timeValue,
                late_threshold_minutes: lateThreshold
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showMessage('settings-message', 'Settings saved successfully!', 'success');
            if (data.last_updated) {
                const lastUpdatedText = document.getElementById('last-updated-text');
                if (lastUpdatedText) lastUpdatedText.textContent = data.last_updated;
            }
            setTimeout(() => {
                loadClassTimeSettings();
            }, 1000);
        } else {
            showMessage('settings-message', data.error || 'Error saving settings', 'error');
        }
    } catch (error) {
        showMessage('settings-message', 'Error connecting to server', 'error');
        console.error('Error:', error);
    }
});

function exportReport() {
    const format = prompt('Export format:\n1. Excel (xlsx)\n2. PDF\n\nEnter 1 or 2:', '1');
    if (!format) return;
    
    const date = prompt('Enter date (YYYY-MM-DD) or leave empty for today:', new Date().toISOString().split('T')[0]);
    if (date === null) return;
    
    const formatType = format === '1' ? 'excel' : 'pdf';
    const url = `/api/reports/daily?date=${date || new Date().toISOString().split('T')[0]}&format=${formatType}`;
    
    window.open(url, '_blank');
}
