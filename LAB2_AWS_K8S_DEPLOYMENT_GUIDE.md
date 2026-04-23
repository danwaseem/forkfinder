# Lab 2 — AWS + Kubernetes Deployment Guide

End-to-end instructions for deploying ForkFinder on AWS EKS.
Follow each section in order. Commands assume macOS/Linux with `bash`.

---

## Prerequisites — install once on your laptop

| Tool | Install command | Version check |
|---|---|---|
| AWS CLI v2 | `brew install awscli` | `aws --version` |
| eksctl | `brew tap weaveworks/tap && brew install weaveworks/tap/eksctl` | `eksctl version` |
| kubectl | `brew install kubectl` | `kubectl version --client` |
| Docker Desktop | download from docker.com | `docker --version` |
| Helm (for LB controller) | `brew install helm` | `helm version` |

---

## Part A — AWS Account Setup

### A1. Create an IAM user for the lab

1. Log in to the AWS Console → **IAM** → **Users** → **Add users**
2. Username: `lab2-student`
3. Attach policies:
   - `AmazonEKSFullAccess`
   - `AmazonEC2FullAccess`
   - `AmazonECRFullAccess`
   - `IAMFullAccess`
   - `AWSCloudFormationFullAccess`
4. Create access key → download the CSV.

### A2. Configure the CLI

```bash
aws configure
# AWS Access Key ID: <from the CSV>
# AWS Secret Access Key: <from the CSV>
# Default region name: us-east-1
# Default output format: json
```

Verify:
```bash
aws sts get-caller-identity
# Should print your account ID and the lab2-student ARN
```

---

## Part B — Create ECR Repositories (one per service image)

```bash
REGION=us-east-1
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

for svc in user-service owner-service restaurant-service review-service frontend; do
  aws ecr create-repository \
    --repository-name forkfinder/${svc} \
    --region ${REGION}
done
```

List repositories to confirm:
```bash
aws ecr describe-repositories --region ${REGION} \
  --query "repositories[*].repositoryUri" --output table
```

**Screenshot to capture:** The ECR console showing all 5 repositories.

---

## Part C — Build and Push Docker Images

From the **repo root** directory:

### C1. Authenticate Docker to ECR

```bash
aws ecr get-login-password --region ${REGION} \
  | docker login --username AWS \
    --password-stdin ${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com
```

### C2. Build and push each image

```bash
ECR=${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com

# User / Reviewer Service
docker build -f services/user-service/Dockerfile \
  -t ${ECR}/forkfinder/user-service:latest .
docker push ${ECR}/forkfinder/user-service:latest

# Restaurant Owner Service
docker build -f services/owner-service/Dockerfile \
  -t ${ECR}/forkfinder/owner-service:latest .
docker push ${ECR}/forkfinder/owner-service:latest

# Restaurant Service
docker build -f services/restaurant-service/Dockerfile \
  -t ${ECR}/forkfinder/restaurant-service:latest .
docker push ${ECR}/forkfinder/restaurant-service:latest

# Review Service
docker build -f services/review-service/Dockerfile \
  -t ${ECR}/forkfinder/review-service:latest .
docker push ${ECR}/forkfinder/review-service:latest

# Frontend (bake the API URL — update with your actual backend hostname after step E)
# For now, leave as localhost; we will rebuild after we get the EKS ALB hostname.
docker build -f frontend/Dockerfile \
  --build-arg VITE_API_URL=http://localhost:8000 \
  -t ${ECR}/forkfinder/frontend:latest \
  frontend/
docker push ${ECR}/forkfinder/frontend:latest
```

**Screenshot to capture:** ECR console showing pushed images with recent push timestamps.

---

## Part D — Create the EKS Cluster

This step takes ~15–20 minutes.

```bash
eksctl create cluster \
  --name forkfinder-cluster \
  --region ${REGION} \
  --nodegroup-name standard-nodes \
  --node-type t3.medium \
  --nodes 2 \
  --nodes-min 1 \
  --nodes-max 3 \
  --with-oidc \
  --managed
```

Update your kubeconfig:
```bash
aws eks update-kubeconfig \
  --region ${REGION} \
  --name forkfinder-cluster
```

Verify the cluster is ready:
```bash
kubectl get nodes
# Should show 2 nodes in Ready state
```

**Screenshot to capture:** `kubectl get nodes` output showing nodes in `Ready` state.

---

## Part E — Install the AWS Load Balancer Controller

The Ingress manifest uses the ALB ingress class. This requires the AWS Load Balancer Controller.

```bash
# Create IAM policy for the controller
curl -o iam_policy.json \
  https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/v2.7.1/docs/install/iam_policy.json

aws iam create-policy \
  --policy-name AWSLoadBalancerControllerIAMPolicy \
  --policy-document file://iam_policy.json

# Create service account with the policy attached
eksctl create iamserviceaccount \
  --cluster=forkfinder-cluster \
  --namespace=kube-system \
  --name=aws-load-balancer-controller \
  --role-name AmazonEKSLoadBalancerControllerRole \
  --attach-policy-arn=arn:aws:iam::${ACCOUNT_ID}:policy/AWSLoadBalancerControllerIAMPolicy \
  --approve \
  --region ${REGION}

# Install via Helm
helm repo add eks https://aws.github.io/eks-charts
helm repo update
helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=forkfinder-cluster \
  --set serviceAccount.create=false \
  --set serviceAccount.name=aws-load-balancer-controller
```

Verify the controller is running:
```bash
kubectl get deployment -n kube-system aws-load-balancer-controller
```

---

## Part F — Update Kubernetes Manifests with Your ECR URIs

Replace the placeholder in every manifest file:

```bash
ECR_URI="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com"

# macOS sed:
for f in kubernetes/04-user-service.yaml \
          kubernetes/05-owner-service.yaml \
          kubernetes/06-restaurant-service.yaml \
          kubernetes/07-review-service.yaml \
          kubernetes/08-frontend.yaml; do
  sed -i '' "s|<YOUR_ECR_REGISTRY>|${ECR_URI}|g" ${f}
done
```

---

## Part G — Create the Secrets File

```bash
cd kubernetes

# Base64-encode your values
SECRET_KEY_B64=$(python3 -c "import secrets,base64; print(base64.b64encode(secrets.token_hex(32).encode()).decode())")

cp 02-secrets.yaml.example 02-secrets.yaml

# macOS sed — substitute the placeholder SECRET_KEY value:
sed -i '' "s|ZGV2LXNlY3JldC1jaGFuZ2UtaW4tcHJvZHVjdGlvbi1taW4tMzItY2hhcnM=|${SECRET_KEY_B64}|g" 02-secrets.yaml

cd ..
```

Confirm `02-secrets.yaml` has your real base64 values (not the placeholders).

---

## Part H — Deploy to Kubernetes

Apply all manifests in order:

```bash
kubectl apply -f kubernetes/00-namespace.yaml
kubectl apply -f kubernetes/01-configmap.yaml
kubectl apply -f kubernetes/02-secrets.yaml
kubectl apply -f kubernetes/03-mongodb.yaml
kubectl apply -f kubernetes/04-user-service.yaml
kubectl apply -f kubernetes/05-owner-service.yaml
kubectl apply -f kubernetes/06-restaurant-service.yaml
kubectl apply -f kubernetes/07-review-service.yaml
kubectl apply -f kubernetes/08-frontend.yaml
kubectl apply -f kubernetes/09-ingress.yaml
```

---

## Part I — Verify All Services Are Running

```bash
# Watch pods come up (Ctrl+C when all are Running)
kubectl get pods -n forkfinder --watch

# Check all deployments
kubectl get deployments -n forkfinder

# Check all services
kubectl get services -n forkfinder

# Check ingress (may take 2–5 min for ALB to provision)
kubectl get ingress -n forkfinder
```

Expected `kubectl get pods -n forkfinder` output (all status = `Running`):
```
NAME                                   READY   STATUS    RESTARTS
frontend-<hash>                        1/1     Running   0
mongodb-<hash>                         1/1     Running   0
owner-service-<hash>                   1/1     Running   0
restaurant-service-<hash>              1/1     Running   0
review-service-<hash>                  1/1     Running   0
user-service-<hash>                    1/1     Running   0
```

**Screenshot to capture:** Full output of `kubectl get pods -n forkfinder` showing all pods Running.

---

## Part J — Rebuild the Frontend with the Real API URL

After the ingress is provisioned, get the ALB hostname:

```bash
ALB_HOST=$(kubectl get ingress forkfinder-ingress -n forkfinder \
  -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
echo "ALB hostname: ${ALB_HOST}"
```

Rebuild and push the frontend image with the real backend URL:

```bash
docker build -f frontend/Dockerfile \
  --build-arg VITE_API_URL=http://${ALB_HOST} \
  -t ${ECR}/forkfinder/frontend:latest \
  frontend/

docker push ${ECR}/forkfinder/frontend:latest

# Trigger a rolling restart so K8s pulls the new image
kubectl rollout restart deployment/frontend -n forkfinder
kubectl rollout status deployment/frontend -n forkfinder
```

---

## Part K — Seed the Database

Connect to the running backend to run the seed script:

```bash
# Get the name of any running backend pod
POD=$(kubectl get pod -n forkfinder -l app=user-service \
  -o jsonpath='{.items[0].metadata.name}')

# Copy and run the seed script
kubectl cp backend/seed_data.py forkfinder/${POD}:/app/seed_data.py
kubectl exec -n forkfinder ${POD} -- python seed_data.py
```

---

## Part L — Validate the Deployment

```bash
# 1. Health check on each service (via the ALB)
curl http://${ALB_HOST}/health

# 2. Login endpoint
curl -X POST http://${ALB_HOST}/auth/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@demo.com","password":"password"}'

# 3. Restaurant search
curl http://${ALB_HOST}/restaurants?q=pizza

# 4. Frontend loads
curl -I http://${ALB_HOST}/
# Should return HTTP 200
```

**Screenshot to capture:**
- Browser showing the ForkFinder frontend at the ALB hostname
- `kubectl get pods -n forkfinder` (all Running)
- `kubectl get services -n forkfinder`
- `kubectl get ingress -n forkfinder` (showing the ALB ADDRESS)

---

## Part M — Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Pod stuck in `Pending` | Insufficient node resources | Scale node group: `eksctl scale nodegroup --cluster forkfinder-cluster --nodes 3 standard-nodes` |
| Pod stuck in `ImagePullBackOff` | Wrong ECR URI or missing ECR permissions | Re-run Part F; check node IAM role has `AmazonEC2ContainerRegistryReadOnly` |
| Pod in `CrashLoopBackOff` | App startup failure | `kubectl logs <pod-name> -n forkfinder` — usually a bad `DATABASE_URL` or missing secret |
| Ingress ADDRESS empty after 10 min | LB controller not running | `kubectl logs -n kube-system -l app.kubernetes.io/name=aws-load-balancer-controller` |
| MongoDB readiness probe failing | Init takes >30s on first boot | `kubectl describe pod mongodb-<hash> -n forkfinder`; increase `initialDelaySeconds` in `03-mongodb.yaml` |
| Frontend shows blank/CORS error | `VITE_API_URL` wrong | Re-run Part J with the correct ALB hostname |

---

## Part N — Tear Down (after grading)

To avoid ongoing AWS charges:

```bash
# Delete all K8s resources
kubectl delete namespace forkfinder

# Delete the EKS cluster (also deletes node EC2 instances)
eksctl delete cluster --name forkfinder-cluster --region ${REGION}

# Optionally delete ECR repositories
for svc in user-service owner-service restaurant-service review-service frontend; do
  aws ecr delete-repository \
    --repository-name forkfinder/${svc} \
    --force --region ${REGION}
done
```

---

## Screenshots Checklist for the Report

| # | Screenshot | Where to capture |
|---|---|---|
| 1 | ECR console — 5 repositories | AWS Console → ECR |
| 2 | EKS cluster overview | AWS Console → EKS → Clusters → forkfinder-cluster |
| 3 | `kubectl get nodes` (Ready) | Terminal |
| 4 | `kubectl get pods -n forkfinder` (all Running) | Terminal |
| 5 | `kubectl get services -n forkfinder` | Terminal |
| 6 | `kubectl get ingress -n forkfinder` (with ADDRESS) | Terminal |
| 7 | ForkFinder frontend running at ALB URL | Browser |
| 8 | Swagger UI at `http://<ALB>/docs` | Browser |
