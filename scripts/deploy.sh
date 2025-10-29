#!/bin/bash
# SoundHash Kubernetes Deployment Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT=${1:-production}
VERSION=${2:-latest}
NAMESPACE="soundhash-${ENVIRONMENT}"
HELM_RELEASE="soundhash"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}SoundHash Kubernetes Deployment${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Environment: ${ENVIRONMENT}"
echo "Version: ${VERSION}"
echo "Namespace: ${NAMESPACE}"
echo ""

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}Error: kubectl is not installed${NC}"
    exit 1
fi

if ! command -v helm &> /dev/null; then
    echo -e "${RED}Error: helm is not installed${NC}"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: docker is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ All prerequisites met${NC}"
echo ""

# Build and push Docker image
echo -e "${YELLOW}Building Docker image...${NC}"
docker build -t ghcr.io/subculture-collective/soundhash:${VERSION} -f Dockerfile.production .

echo -e "${YELLOW}Pushing Docker image...${NC}"
docker push ghcr.io/subculture-collective/soundhash:${VERSION}

echo -e "${GREEN}✓ Docker image built and pushed${NC}"
echo ""

# Create namespace if it doesn't exist
echo -e "${YELLOW}Creating namespace...${NC}"
kubectl create namespace ${NAMESPACE} --dry-run=client -o yaml | kubectl apply -f -

echo -e "${GREEN}✓ Namespace ready${NC}"
echo ""

# Deploy with Helm
echo -e "${YELLOW}Deploying with Helm...${NC}"
helm upgrade --install ${HELM_RELEASE} ./helm/soundhash \
  --namespace ${NAMESPACE} \
  --create-namespace \
  --set image.tag=${VERSION} \
  --values ./helm/soundhash/values-${ENVIRONMENT}.yaml \
  --wait \
  --timeout 10m \
  --debug

echo -e "${GREEN}✓ Helm deployment complete${NC}"
echo ""

# Wait for deployment to be ready
echo -e "${YELLOW}Waiting for pods to be ready...${NC}"
kubectl wait --for=condition=available --timeout=300s \
  deployment/${HELM_RELEASE}-api \
  -n ${NAMESPACE}

echo -e "${GREEN}✓ Pods are ready${NC}"
echo ""

# Run database migrations
echo -e "${YELLOW}Running database migrations...${NC}"
POD_NAME=$(kubectl get pods -n ${NAMESPACE} -l app.kubernetes.io/name=soundhash,component=api -o jsonpath='{.items[0].metadata.name}')

if [ -n "$POD_NAME" ]; then
    kubectl exec -n ${NAMESPACE} ${POD_NAME} -- alembic upgrade head
    echo -e "${GREEN}✓ Database migrations complete${NC}"
else
    echo -e "${YELLOW}⚠ Could not find pod for migrations${NC}"
fi
echo ""

# Verify deployment
echo -e "${YELLOW}Verifying deployment...${NC}"
kubectl rollout status deployment/${HELM_RELEASE}-api -n ${NAMESPACE}

# Get service information
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment Information${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Pods:"
kubectl get pods -n ${NAMESPACE} -l app.kubernetes.io/name=soundhash

echo ""
echo "Services:"
kubectl get services -n ${NAMESPACE}

echo ""
echo "Ingress:"
kubectl get ingress -n ${NAMESPACE}

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "To view logs:"
echo "  kubectl logs -f -n ${NAMESPACE} -l app.kubernetes.io/name=soundhash"
echo ""
echo "To port-forward to the service:"
echo "  kubectl port-forward -n ${NAMESPACE} svc/${HELM_RELEASE}-api-service 8000:80"
echo ""
echo "To scale the deployment:"
echo "  kubectl scale deployment/${HELM_RELEASE}-api -n ${NAMESPACE} --replicas=5"
echo ""
