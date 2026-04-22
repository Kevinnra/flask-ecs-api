# Flask ECS API

A containerized Python REST API deployed on AWS ECS Fargate with RDS PostgreSQL, Application Load Balancer, and a fully automated CI/CD pipeline using GitHub Actions and OIDC authentication.

---

## Architecture

```
Internet
    │
    ▼
Internet Gateway
    │
    ▼  (public subnets: ap-northeast-1a, 1c)
Application Load Balancer  ←──── GitHub Actions (CI/CD)
    │                                    │
    ▼                              ECR (image registry)
ECS Fargate  ──── NAT Gateway           │
(Flask API)  ◄──────────────────────────┘
    │                (image pull)
    ▼
RDS PostgreSQL
(private subnets: ap-northeast-1a, 1c)

Secrets Manager → DB credentials injected at runtime
CloudWatch Logs → Container stdout/stderr
```

**Key security principle:** The application and database have no direct internet access. Only the ALB lives in public subnets. Everything else is behind it in private subnets.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Application | Python, Flask, Gunicorn, SQLAlchemy |
| Containerization | Docker (linux/amd64), ECR |
| Compute | ECS Fargate |
| Database | RDS PostgreSQL (db.t3.micro) |
| Networking | VPC, public/private subnets, IGW, NAT Gateway, Security Groups |
| Load Balancing | Application Load Balancer |
| Secrets | AWS Secrets Manager |
| CI/CD | GitHub Actions with OIDC (no stored credentials) |
| Logging | CloudWatch Logs |

---

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/` | GET | Returns request count from DB |
| `/health` | GET | Health check (used by ALB) |
| `/status` | GET | Environment and DB host info |
| `/init-db` | GET | Creates database tables |

---

## Project Structure

```
flask-ecs-api/
├── app/
│   ├── main.py              # Flask application
│   └── requirements.txt     # Python dependencies
├── .github/
│   └── workflows/
│       └── deploy.yml       # CI/CD pipeline
├── Dockerfile               # Container definition
├── .dockerignore
└── task-definition.json     # ECS task definition
```

---

## CI/CD Pipeline

Every push to `main` triggers the pipeline automatically:

```
1. Authenticate to AWS via OIDC (no stored credentials)
2. Build Docker image for linux/amd64 (cross-platform)
3. Tag with Git commit SHA + latest
4. Push to ECR
5. Pull current task definition
6. Update image reference
7. Deploy to ECS — waits for service stability
```

No AWS credentials are stored in GitHub. The pipeline uses OIDC to assume a role at runtime with least-privilege permissions.

---

## Infrastructure

Built entirely using AWS CLI commands. Key networking concepts applied:

**VPC Design:**
- `/16` CIDR block giving 65,536 addresses
- Two public subnets across two AZs for ALB high availability
- Two private subnets across two AZs for ECS and RDS
- NAT Gateway allows ECS tasks outbound access without a public IP

**Security Groups (least-privilege):**
- ALB SG: accepts port 80 from `0.0.0.0/0`
- ECS SG: accepts port 5000 from ALB SG only
- RDS SG: accepts port 5432 from ECS SG only

**Secrets:**
- DB credentials stored in AWS Secrets Manager
- ECS pulls secrets at task startup via IAM role
- No credentials in code, task definition, or environment variables

---

## Running Locally

```bash
# Build for local testing
docker build -t flask-api:local .

# Run with environment variables
docker run -p 8080:5000 \
  -e ENVIRONMENT=local \
  -e DB_HOST=localhost \
  flask-api:local

# Test endpoints
curl http://localhost:8080/health
curl http://localhost:8080/
curl http://localhost:8080/status
```

**Note:** Apple Silicon users must use `--platform linux/amd64` for ECS-compatible builds:

```bash
docker buildx build --platform linux/amd64 -t flask-api:v1 .
```

---

## Key Learnings

- **Container platform mismatch**: Apple Silicon builds `arm64` by default. ECS requires `linux/amd64`. Always specify `--platform` explicitly, or automate it in CI/CD.
- **`0.0.0.0` binding**: Flask must bind to `0.0.0.0` to accept connections from outside the container. `127.0.0.1` only accepts connections from within the container itself.
- **Private subnets need NAT**: Resources in private subnets have no path to the internet by default. NAT Gateway lives in a public subnet and provides outbound-only internet access for private resources.
- **Security group chaining**: Instead of opening ports to IP ranges, referencing another security group as the source allows permissions to follow the resource regardless of IP changes.
- **OIDC over stored credentials**: GitHub OIDC eliminates the need to store AWS access keys. GitHub gets a short-lived token valid only for that workflow run.

---

## Deployment Order

When rebuilding from scratch:

1. VPC + subnets + IGW + NAT Gateway + route tables
2. Security groups
3. RDS subnet group + RDS instance
4. ECR repository + push initial image
5. ECS cluster + task definition + service
6. ALB + target group + listener
7. Update ECS service with ALB

Teardown order (reverse): ECS service → NAT Gateway → EIP release → ALB → RDS (if removing).

---

## Cost Notes

Approximate monthly cost when running continuously:

| Resource | Cost |
|---|---|
| ECS Fargate (0.25 vCPU, 0.5GB) | ~$9 |
| RDS db.t3.micro | ~$15 |
| ALB | ~$18 |
| NAT Gateway | ~$33 |
| **Total** | **~$75/month** |


## Author

Build with ☁️ by Kevinn Ramirez - [Web Portfolio](https://www.kevinnramirez.com)
