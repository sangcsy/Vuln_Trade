# EC2 Deployment

This project can be deployed to one EC2 instance with Docker Compose. GitHub Actions connects to the instance over SSH, pulls the latest `dev` branch, and restarts the Compose stack.

## EC2 Requirements

- Ubuntu EC2 instance, or another Linux image with Docker Compose plugin support
- Inbound security group rules:
  - TCP 22 from your admin IP or GitHub Actions runner access path
  - TCP 80 from allowed users
- Docker, Docker Compose plugin, and Git installed

Example Ubuntu setup:

```bash
sudo apt update
sudo apt install -y git docker.io docker-compose-plugin
sudo usermod -aG docker $USER
```

Log out and back in after adding the user to the `docker` group.

## First-Time App Setup

```bash
git clone --branch dev https://github.com/sangcsy/Vuln_Trade.git ~/Vuln_Trade
cd ~/Vuln_Trade
cp .env.example .env
```

Edit `~/Vuln_Trade/.env` on the EC2 instance for the deployment environment. Do not commit `.env`.

Start manually once if needed:

```bash
docker compose up -d --build
```

The app is served through Nginx on port 80.

## GitHub Secrets

Create these repository secrets:

```text
EC2_HOST      EC2 public IP address or DNS name
EC2_USER      SSH user, for example ubuntu or ec2-user
EC2_SSH_KEY   Private key used to SSH into the instance
```

Optional secrets:

```text
EC2_PORT      SSH port, defaults to 22
EC2_APP_DIR   App directory on EC2, defaults to ~/Vuln_Trade
```

## Automatic Deployment

The workflow in `.github/workflows/deploy-ec2.yml` runs on pushes to `dev` and can also be started manually from GitHub Actions.

Deployment commands executed on EC2:

```bash
git fetch origin dev
git checkout dev
git pull --ff-only origin dev
docker compose up -d --build
docker image prune -f
```

## Operational Notes

- MySQL is not exposed outside Docker Compose.
- The `db-data` Docker volume stores MySQL data on the EC2 instance.
- Uploaded files are stored under `app/src/static/uploads` on the EC2 working tree.
- Back up the Docker volume and uploads directory before replacing or terminating the EC2 instance.
