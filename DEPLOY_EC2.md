# EC2 Deployment

This project deploys to one EC2 instance with Docker Compose. GitHub Actions uses AWS OIDC to assume an IAM role, then runs deployment commands on EC2 through AWS Systems Manager Run Command. SSH does not need to be open for GitHub Actions.

## Runtime Shape

```text
GitHub push to dev
  -> GitHub Actions
  -> AWS OIDC role
  -> SSM Run Command
  -> EC2 docker compose up -d --build
```

The app is served through Nginx on port 80.

## EC2 Requirements

- Amazon Linux or another Linux image with SSM Agent support
- Docker, Docker Compose plugin, and Git installed
- EC2 IAM role attached with SSM permissions
- Inbound security group rules:
  - TCP 80 from allowed users
  - TCP 22 only from your admin IP, or closed if you use SSM Session Manager

For Amazon Linux:

```bash
sudo dnf update -y
sudo dnf install -y git docker
sudo systemctl enable --now docker
sudo usermod -aG docker ec2-user
```

If `docker compose` is unavailable:

```bash
mkdir -p ~/.docker/cli-plugins
curl -SL https://github.com/docker/compose/releases/download/v2.29.7/docker-compose-linux-x86_64 -o ~/.docker/cli-plugins/docker-compose
chmod +x ~/.docker/cli-plugins/docker-compose
docker compose version
```

Log out and back in after adding the user to the `docker` group.

## First-Time App Setup

```bash
git clone --branch dev https://github.com/sangcsy/Vuln_Trade.git ~/Vuln_Trade
cd ~/Vuln_Trade
cp .env.example .env
docker compose up -d --build
```

Edit `~/Vuln_Trade/.env` on the EC2 instance for the deployment environment. Do not commit `.env`.

## AWS Setup

### 1. Attach an EC2 Role for SSM

Create or choose an IAM role for the EC2 instance:

```text
Trusted entity: AWS service
Use case: EC2
Policy: AmazonSSMManagedInstanceCore
```

Attach it to the instance:

```text
EC2 Console
-> Instances
-> select instance
-> Actions
-> Security
-> Modify IAM role
```

Wait a few minutes, then confirm the instance appears in:

```text
AWS Systems Manager
-> Fleet Manager
```

If it does not appear, confirm SSM Agent is running:

```bash
sudo systemctl status amazon-ssm-agent
sudo systemctl enable --now amazon-ssm-agent
```

### 2. Create the GitHub OIDC Provider

In IAM, create an OpenID Connect identity provider:

```text
Provider URL: https://token.actions.githubusercontent.com
Audience: sts.amazonaws.com
```

If this provider already exists in the account, reuse it.

### 3. Create a GitHub Actions Deploy Role

Create an IAM role trusted by the GitHub OIDC provider. Limit it to this repository and the `dev` branch.

Trust policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::<AWS_ACCOUNT_ID>:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
          "token.actions.githubusercontent.com:sub": "repo:sangcsy/Vuln_Trade:ref:refs/heads/dev"
        }
      }
    }
  ]
}
```

Replace `<AWS_ACCOUNT_ID>` with your AWS account ID.

Attach this permissions policy to the role. Replace region, account ID, and instance ID if you want to scope it tightly.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "ssm:SendCommand",
      "Resource": [
        "arn:aws:ssm:<AWS_REGION>::document/AWS-RunShellScript",
        "arn:aws:ec2:<AWS_REGION>:<AWS_ACCOUNT_ID>:instance/<EC2_INSTANCE_ID>"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "ssm:GetCommandInvocation",
        "ssm:ListCommandInvocations",
        "ssm:ListCommands"
      ],
      "Resource": "*"
    }
  ]
}
```

## GitHub Secrets

Create these repository secrets:

```text
AWS_REGION       Example: ap-northeast-2
AWS_ROLE_ARN     ARN of the GitHub Actions deploy role
EC2_INSTANCE_ID  Example: i-0123456789abcdef0
```

Optional secret:

```text
EC2_DEPLOY_USER  Linux user that owns the app checkout. Defaults to ec2-user.
EC2_APP_DIR      App directory on EC2. Defaults to the deploy user's ~/Vuln_Trade.
```

SSH secrets are no longer required for automatic deployment.

## Automatic Deployment

The workflow in `.github/workflows/deploy-ec2.yml` runs on pushes to `dev` and can also be started manually from GitHub Actions.

Deployment commands executed on EC2:

```bash
cd /home/ec2-user/Vuln_Trade
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
