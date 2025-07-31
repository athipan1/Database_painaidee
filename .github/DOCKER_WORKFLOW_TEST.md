# Docker CI/CD Workflow Test

This file was created to test the Docker CI/CD workflow implementation.

## Workflow Features Implemented

✅ **Automatic Triggers**
- Triggers on push to main branch
- Triggers on pull requests targeting main branch

✅ **Docker Registry Support**
- Default: GitHub Container Registry (ghcr.io)
- Alternative: Docker Hub (configurable via secrets)

✅ **Smart Tagging Strategy**
- `latest` tag for main branch builds
- `main-<commit-sha>` for specific commits
- `pr-<number>` for pull request builds

✅ **Multi-Platform Builds**
- linux/amd64 (Intel/AMD)
- linux/arm64 (ARM including Apple Silicon)

✅ **Optimization Features**
- Docker layer caching
- Only pushes on main branch (PRs build but don't push)
- Buildx multi-platform support

## Testing Instructions

1. This workflow will automatically run when:
   - This PR is merged to main branch
   - Any future pushes to main branch
   - Any new pull requests are opened

2. Check workflow runs at: `Actions` tab in GitHub repository

3. Verify images are pushed to: `ghcr.io/athipan1/database_painaidee`

## Registry Configuration

### Default (GitHub Container Registry)
No additional configuration needed. Images automatically pushed to:
```
ghcr.io/athipan1/database_painaidee:latest
ghcr.io/athipan1/database_painaidee:main-<sha>
```

### Alternative (Docker Hub)
Set these repository secrets:
- `DOCKER_REGISTRY`: `docker.io`
- `DOCKER_USERNAME`: Your Docker Hub username
- `DOCKER_PASSWORD`: Your Docker Hub token