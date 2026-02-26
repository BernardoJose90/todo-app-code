# Todo App - Application Code

This repository contains the Flask-based Todo application.

## 🏗️ Architecture

- Flask web application with SQLAlchemy
- RDS MySQL database (production)
- ECR for container images
- GitOps deployment with ArgoCD

## 🚀 CI/CD Pipeline

On push to `main` branch:
1. Builds Docker image
2. Pushes to ECR (`production/todoapp`)
3. Updates the GitOps repository with new image tag
4. ArgoCD automatically deploys to EKS

## 📦 Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
python main.py