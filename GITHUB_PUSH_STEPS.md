# Steps to Push to GitHub

## ✅ Already Completed:
- ✅ Git repository initialized
- ✅ Files staged and committed
- ✅ Initial commit created

## Next Steps:

### 1. Create GitHub Repository
1. Go to https://github.com and sign in
2. Click the **"+"** icon (top right) → **"New repository"**
3. Repository name: `face-recognition-attendance` (or your preferred name)
4. Description: "Face recognition attendance system with slot-based timetable"
5. Choose **Public** or **Private**
6. **DO NOT** check "Initialize with README" (we already have files)
7. Click **"Create repository"**

### 2. Add Remote and Push

After creating the repository, GitHub will show you commands. Use these:

**Replace `YOUR_USERNAME` and `REPO_NAME` with your actual values:**

```bash
# Add the remote repository
git remote add origin https://github.com/YOUR_USERNAME/REPO_NAME.git

# Rename branch to main (if needed)
git branch -M main

# Push to GitHub
git push -u origin main
```

### Example:
If your username is `johndoe` and repo name is `face-recognition-attendance`:

```bash
git remote add origin https://github.com/johndoe/face-recognition-attendance.git
git branch -M main
git push -u origin main
```

### 3. Authentication

When you push, GitHub will ask for authentication:
- **Option A**: Use GitHub Personal Access Token (recommended)
  - Go to: Settings → Developer settings → Personal access tokens → Tokens (classic)
  - Generate new token with `repo` scope
  - Use token as password when prompted

- **Option B**: Use GitHub CLI
  ```bash
  gh auth login
  ```

### 4. Verify

After pushing, refresh your GitHub repository page. You should see all your files!

## Future Updates

For future changes:

```bash
git add .
git commit -m "Your commit message"
git push
```

## Troubleshooting

If you get "remote origin already exists":
```bash
git remote remove origin
git remote add origin https://github.com/YOUR_USERNAME/REPO_NAME.git
```

If you need to change the remote URL:
```bash
git remote set-url origin https://github.com/YOUR_USERNAME/REPO_NAME.git
```

