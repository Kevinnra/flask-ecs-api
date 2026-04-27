# Flask ECS API

A containerized Python REST API deployed on AWS ECS Fargate — demonstrates secure multi-tier architecture with private networking, managed database, and fully automated CI/CD.

![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-000000?style=flat&logo=flask&logoColor=white)
![AWS ECS](https://img.shields.io/badge/ECS_Fargate-FF9900?style=flat&logo=amazon-aws&logoColor=white)
![AWS RDS](https://img.shields.io/badge/RDS_PostgreSQL-527FFF?style=flat&logo=amazon-rds&logoColor=white)
![AWS ALB](https://img.shields.io/badge/ALB-FF9900?style=flat&logo=amazon-aws&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-2088FF?style=flat&logo=github-actions&logoColor=white)

[Portfolio Page](https://kevinnramirez.com/projects/project-v3.html?id=flask-ecs-api) · [LinkedIn](https://linkedin.com/in/kevinnramirez)

> **Note:** The AWS infrastructure for this project (ECS service, RDS, ALB, NAT Gateway) has been torn down to avoid ongoing costs. The architecture and documentation reflect the fully working system that was deployed and tested. The application runs locally following the instructions below.

---

## Architecture

![Architecture Diagram](./Resources/images/flask-ecs-architecture.jpg)

Traffic enters the VPC through an Internet Gateway and reaches the Application Load Balancer in the public subnets. The ALB forwards requests to ECS Fargate tasks running in private subnets, which connect to RDS PostgreSQL also isolated in private subnets. The design keeps the application and database completely unreachable from the internet — only the load balancer is public-facing.

---

## Live API

Screenshots taken from the running system before teardown:

| Endpoint | Screenshot |
|---|---|
| `GET /` — request counter from RDS | ![root endpoint](./Resources/images/screenshot-root.jpg) |
| `GET /health` — ALB health check | ![health endpoint](./Resources/images/screenshot-health.jpg) |
| `GET /status` — environment info | ![status endpoint](./Resources/images/screenshot-status.jpg) |

---

## Tech Stack

| Service | Purpose |
|---|---|
| Python 3.12 + Flask | REST API application |
| Gunicorn | Production WSGI server inside the container |
| Docker + ECR | Container image build and registry |
| ECS Fargate | Serverless container compute — no EC2 to manage |
| Application Load Balancer | Public traffic entry point, health checks |
| RDS PostgreSQL (db.t3.micro) | Managed relational database in private subnet |
| VPC | Isolated network — public and private subnets across 2 AZs |
| NAT Gateway | Outbound internet access for private subnet resources |
| AWS Secrets Manager | Encrypted storage for database credentials |
| IAM (OIDC + execution role) | Least-privilege access for CI/CD and ECS tasks |
| CloudWatch Logs | Container stdout/stderr aggregation |
| GitHub Actions | CI/CD pipeline — build, push, deploy on every push to main |

---

## Features

- Built a custom VPC with public/private subnet separation across two Availability Zones
- Deployed ECS Fargate service in private subnets with no public IP assigned to tasks
- Configured Application Load Balancer with `/health` endpoint health checks before routing traffic
- Implemented three-layer security group chain — ALB → ECS → RDS, each tier only reachable from the tier above
- Stored database credentials in Secrets Manager and injected them at container startup via IAM execution role
- Automated full CI/CD pipeline with GitHub Actions using OIDC — no AWS credentials stored anywhere
- Built Docker images cross-compiled for `linux/amd64` to ensure ECS compatibility from Apple Silicon

---

## Project Structure

<details>
<summary>View file tree</summary>

```
flask-ecs-api/
├── app/
│   ├── main.py              # Flask app — endpoints, SQLAlchemy models, env var config
│   └── requirements.txt     # Python dependencies: Flask, gunicorn, psycopg2, SQLAlchemy
├── .github/
│   └── workflows/
│       └── deploy.yml       # CI/CD pipeline — build linux/amd64 image, push to ECR, deploy to ECS
├── Dockerfile               # Container build — python:3.12-slim base, gunicorn entrypoint
├── .dockerignore            # Excludes __pycache__, .env, .git from image context
└── task-definition.json     # ECS task definition — CPU, memory, env vars, Secrets Manager refs
```

</details>

---

## How to Run Locally

**Prerequisites:** Docker Desktop, Python 3.12+

```bash
# Clone the repo
git clone https://github.com/Kevinnra/flask-ecs-api.git
cd flask-ecs-api
```

```bash
# Build the image
docker build -t flask-api:local .
```

```bash
# Run with environment variables
docker run -p 8080:5000 \
  -e ENVIRONMENT=local \
  flask-api:local
```

**Expected output:**
```
[INFO] Starting gunicorn 22.0.0
[INFO] Listening at: http://0.0.0.0:5000
[INFO] Booting worker with pid: 8
[INFO] Booting worker with pid: 9
```

```bash
# Test the endpoints
curl http://localhost:8080/health
# {"status": "healthy", "timestamp": "2026-04-16T..."}

curl http://localhost:8080/
# {"environment": "local", "message": "Flask API running on ECS", "version": "3.0", ...}

curl http://localhost:8080/status
# {"app": "flask-ecs-api", "db_host": "not-configured", "region": "not-configured"}
```

> **Apple Silicon:** Use `docker buildx build --platform linux/amd64 -t flask-api:local .` for an ECS-compatible build.

---

## Key Decisions

- **Chose ECS Fargate over EC2** — no instance management needed; the learning goal was container orchestration, not server administration
- **Chose OIDC over stored IAM credentials in GitHub** — GitHub gets a short-lived token per workflow run instead of long-lived access keys that need rotation and can leak
- **Chose Secrets Manager over plain env vars in the task definition** — task definitions are visible to anyone with IAM describe permissions; credentials should never appear in plain text there
- **Chose NAT Gateway over VPC Endpoints** — VPC Endpoints are cheaper for production but require per-service configuration; NAT Gateway is simpler for a learning project that tears down between sessions
- **Chose security group chaining over CIDR-based rules** — referencing a security group as the source means permissions follow resources automatically, regardless of IP changes

---

## Challenges and Solutions

- **Problem:** ECS service stuck at 0 running tasks with error `image manifest does not contain descriptor matching platform linux/amd64` → **Solution:** Apple Silicon builds `arm64` images by default; ECS requires `linux/amd64`. Added `--platform linux/amd64` to the build command and baked it into the GitHub Actions workflow permanently so it is never forgotten.

- **Problem:** ECS tasks in private subnets failed to pull images from ECR — no error in the app logs → **Solution:** Private subnets have no route to the internet by default. Deployed a NAT Gateway in the public subnet and added a `0.0.0.0/0` route in the private route table pointing to it. The failure was only visible in ECS service events, not CloudWatch — learned to check the right layer first.

- **Problem:** Database password in plain text in `task-definition.json` after first working deploy → **Solution:** Moved credentials to Secrets Manager, updated the task definition to use `"secrets"` with `valueFrom` referencing the secret ARN, and scoped the IAM execution role policy to that specific ARN. No app code changes needed — Flask still reads `os.getenv()`.

---

## Cost Breakdown

Infrastructure was torn down after the project was complete. Costs below are estimates based on AWS Pricing Calculator for `ap-northeast-1`.

| Service | Est. Monthly Cost | Note |
|---|---|---|
| ECS Fargate (0.25 vCPU / 512 MB) | ~$8.90/mo | Charged per vCPU-hour and GB-hour — cost drops to $0 when tasks are stopped |
| NAT Gateway | ~$32.85/mo | Charged $0.045/hr regardless of traffic — the largest cost driver; replaceable with VPC Endpoints |
| Application Load Balancer | ~$5.84/mo | Charged $0.008/hr plus LCU usage — minimal at dev traffic |
| RDS PostgreSQL (db.t3.micro) | ~$0.00/mo | Free tier eligible for first 12 months; ~$13.00/mo after |
| AWS Secrets Manager | ~$0.40/mo | $0.40 per secret per month regardless of retrieval count |
| Amazon ECR | ~$0.10/mo | First 500 MB of private storage free; a Flask image stays well under that |
| GitHub Actions | $0.00/mo | Free for public repositories |
| **Total** | **~$48.09/mo** | |

Dev/learning setup — the NAT Gateway alone is 68% of the cost. Replacing it with VPC Endpoints for ECR and Secrets Manager would significantly reduce this for a production environment.

---

## Lessons Learned

- The NAT Gateway cost surprised me — it is the most expensive component in a basic VPC and charges by the hour whether tasks are running or not. Knowing when to replace it with VPC Endpoints is a real cost optimization question in cloud roles
- Security group chaining made least-privilege networking concrete: instead of thinking "what IP ranges can reach this resource," I thought "what other resource is allowed to reach this one" — a cleaner mental model
- Debugging containerized deployments requires knowing which layer broke. CloudWatch Logs for app errors, ECS service events for deployment failures, route tables for network issues. I wasted time looking in CloudWatch when the failure was in the ECS service events
- OIDC authentication for CI/CD is simpler than managing IAM users — no keys to create, rotate, or accidentally commit. It should be the default for any pipeline
- `0.0.0.0` in Flask is about network interfaces, not ports — without it the app only listens to itself inside the container and `docker run -p` has no effect

---
## Links

[kevinnramirez.com](https://kevinnramirez.com) · [Portfolio Page](https://kevinnramirez.com/projects/project-v3.html?id=flask-ecs-api) · [LinkedIn](https://linkedin.com/in/kevinnramirez)

---

**Built with ☁️ by Kevin Ramirez** | Cloud Engineer