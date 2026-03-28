# Flask ECS API

A containerized Python REST API deployed on AWS ECS Fargate with a secure VPC, RDS PostgreSQL database, and automated CI/CD pipeline.

> 🚧 Currently under active development

## Stack

Docker · Python Flask · Amazon ECS Fargate · ECR · RDS PostgreSQL · VPC · ALB · GitHub Actions

## Architecture
```
GitHub Actions → ECR → ECS Fargate → RDS PostgreSQL
                           ↑
                    Application Load Balancer
                           ↑
                         Internet
```

## Project Goals

- Containerize a Python Flask REST API using Docker
- Deploy on ECS Fargate inside a properly configured VPC
- Connect to a managed PostgreSQL database on RDS
- Automate build and deployment with GitHub Actions CI/CD

## Status

| Stage | Description | Status |
|-------|-------------|--------|
| 1 | Docker & Flask app | Done ✅ |
| 2 | Push image to ECR | Done ✅ |
| 3 | VPC & Networking | In Progress 🔄 |
| 4 | RDS Database | ⏳ Pending |
| 5 | ECS Fargate deployment | ⏳ Pending |
| 6 | Application Load Balancer | ⏳ Pending |
| 7 | CI/CD Pipeline | ⏳ Pending |

## Author

Build with ☁️ by Kevinn Ramirez - [Web Portfolio](https://www.kevinnramirez.com)
