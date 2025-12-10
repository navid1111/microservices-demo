# 🔍 Complete Verification Guide

Let's check everything step-by-step with expected outputs!

---

## ✅ Step 1: Check All Pods are Running

```bash
kubectl get pods --all-namespaces
```

**Expected Output:**

```
NAMESPACE     NAME                                      READY   STATUS    RESTARTS   AGE
default       api-gateway-xxxxxxxxx-xxxxx               1/1     Running   0          10m
default       order-service-xxxxxxxxx-xxxxx             1/1     Running   0          10m
default       order-service-xxxxxxxxx-yyyyy             1/1     Running   0          10m
default       product-service-xxxxxxxxx-xxxxx           1/1     Running   0          10m
default       product-service-xxxxxxxxx-yyyyy           1/1     Running   0          10m
default       mongodb-xxxxxxxxx-xxxxx                   1/1     Running   0          15m
default       postgres-xxxxxxxxx-xxxxx                  1/1     Running   0          15m
monitoring    prometheus-operator-xxxxxxxxx-xxxxx       1/1     Running   0          5m
```

**What to look for:**

- ✅ All pods should show `Running`
- ✅ READY should be `1/1` (or `2/2` for some)
- ❌ If you see `CrashLoopBackOff`, `ImagePullBackOff`, or `Pending` → Issue!

---

## ✅ Step 2: Check Services in Default Namespace

```bash
kubectl get svc
```

**Expected Output:**

```
NAME                      TYPE           CLUSTER-IP       EXTERNAL-IP   PORT(S)          AGE
api-gateway               LoadBalancer   10.96.x.x        <pending>     80:30xxx/TCP     10m
api-gateway-metrics       ClusterIP      10.96.x.x        <none>        3000/TCP         5m
order-service             ClusterIP      10.96.x.x        <none>        3001/TCP         10m
order-service-metrics     ClusterIP      10.96.x.x        <none>        3001/TCP         5m
product-service           ClusterIP      10.96.x.x        <none>        8000/TCP         10m
product-service-metrics   ClusterIP      10.96.x.x        <none>        8000/TCP         5m
mongodb                   ClusterIP      10.96.x.x        <none>        27017/TCP        15m
postgres                  ClusterIP      10.96.x.x        <none>        5432/TCP         15m
kubernetes                ClusterIP      10.96.0.1        <none>        443/TCP          1h
```

**What to look for:**

- ✅ All your application services exist
- ✅ All 3 `-metrics` services exist (for Prometheus scraping)
- ✅ Database services exist

---

## ✅ Step 3: Check Services in Monitoring Namespace

```bash
kubectl get svc -n monitoring
```

**Expected Output:**

```
NAME                  TYPE        CLUSTER-IP    EXTERNAL-IP   PORT(S)    AGE
prometheus-operator   ClusterIP   10.96.x.x     <none>        8080/TCP   5m
```

**Note:** Since you only installed Prometheus Operator (not the full stack), you won't see Grafana or Prometheus services here yet.

---

## ✅ Step 4: Check ServiceMonitors are Created

```bash
kubectl get servicemonitors -n monitoring
```

**Expected Output:**

```
NAME                      AGE
api-gateway-monitor       5m
order-service-monitor     5m
product-service-monitor   5m
```

**What to look for:**

- ✅ All 3 ServiceMonitors exist
- ✅ They're in the `monitoring` namespace

---

## ✅ Step 5: Check ServiceMonitor Details

```bash
kubectl describe servicemonitor api-gateway-monitor -n monitoring
```

**Expected Output:**

```
Name:         api-gateway-monitor
Namespace:    monitoring
Labels:       release=prometheus
Annotations:  <none>
API Version:  monitoring.coreos.com/v1
Kind:         ServiceMonitor
Metadata:
  ...
Spec:
  Endpoints:
    Interval:  30s
    Path:      /metrics
    Port:      metrics
  Namespace Selector:
    Match Names:
      default
  Selector:
    Match Labels:
      app:  api-gateway
Events:     <none>
```

**What to look for:**

- ✅ Path is `/metrics`
- ✅ Port is `metrics`
- ✅ Namespace selector points to `default`
- ✅ Selector matches your service label `app: api-gateway`

---

## ✅ Step 6: Test Metrics Endpoints Directly

### **6.1: Test API Gateway Metrics**

```bash
kubectl port-forward svc/api-gateway 3000:80 &
sleep 2
curl http://localhost:3000/metrics
```

**Expected Output (partial):**

```
# HELP process_cpu_user_seconds_total Total user CPU time spent in seconds.
# TYPE process_cpu_user_seconds_total counter
process_cpu_user_seconds_total 0.156

# HELP http_request_duration_seconds Duration of HTTP requests in seconds
# TYPE http_request_duration_seconds histogram
http_request_duration_seconds_bucket{le="0.005",method="GET",route="/health",status="200"} 1
http_request_duration_seconds_bucket{le="0.01",method="GET",route="/health",status="200"} 1
...
```

**What to look for:**

- ✅ Should see Prometheus metrics format
- ✅ Should see `http_request_duration_seconds` metrics
- ✅ No errors (404, connection refused, etc.)

**Kill the port-forward:**

```bash
pkill -f "port-forward svc/api-gateway"
```

---

### **6.2: Test Product Service Metrics**

```bash
kubectl port-forward svc/product-service 8000:8000 &
sleep 2
curl http://localhost:8000/metrics
```

**Expected Output (partial):**

```
# HELP product_service_requests_total Total requests
# TYPE product_service_requests_total counter
product_service_requests_total{endpoint="/health",method="GET",status="200"} 5.0

# HELP product_service_request_duration_seconds Request duration
# TYPE product_service_request_duration_seconds histogram
...
```

**Kill the port-forward:**

```bash
pkill -f "port-forward svc/product-service"
```

---

### **6.3: Test Order Service Metrics**

```bash
kubectl port-forward svc/order-service 3001:3001 &
sleep 2
curl http://localhost:3001/metrics
```

**Expected Output (partial):**

```
# HELP order_service_requests_total Total number of requests
# TYPE order_service_requests_total counter
order_service_requests_total{method="GET",route="/health",status="200"} 3

# HELP nodejs_heap_size_total_bytes Process heap size from Node.js in bytes.
...
```

**Kill the port-forward:**

```bash
pkill -f "port-forward svc/order-service"
```

---

## ✅ Step 7: Check Application Health Endpoints

```bash
# Port forward API Gateway
kubectl port-forward svc/api-gateway 3000:80 &
sleep 2

# Test health endpoints
curl http://localhost:3000/health
```

**Expected Output:**

```json
{
  "status": "healthy",
  "service": "api-gateway",
  "timestamp": "2024-12-10T12:30:45.123Z"
}
```

```bash
# Test product service through gateway
curl http://localhost:3000/api/products
```

**Expected Output:**

```json
[]
```

_Empty array is fine - no products created yet_

```bash
# Test order service through gateway
curl http://localhost:3000/api/orders
```

**Expected Output:**

```json
[]
```

**Kill the port-forward:**

```bash
pkill -f "port-forward svc/api-gateway"
```

---

## ✅ Step 8: Test End-to-End Flow

```bash
# Port forward API Gateway
kubectl port-forward svc/api-gateway 3000:80 &
sleep 2

# Create a product
curl -X POST http://localhost:3000/api/products \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Laptop",
    "description": "Gaming laptop for testing",
    "price": 1299.99,
    "stock": 10
  }'
```

**Expected Output:**

```json
{
  "name": "Test Laptop",
  "description": "Gaming laptop for testing",
  "price": 1299.99,
  "stock": 10,
  "id": "675853a1b2c3d4e5f6789abc"
}
```

**Note the `id` value!**

```bash
# Get all products
curl http://localhost:3000/api/products
```

**Expected Output:**

```json
[
  {
    "name": "Test Laptop",
    "description": "Gaming laptop for testing",
    "price": 1299.99,
    "stock": 10,
    "id": "675853a1b2c3d4e5f6789abc"
  }
]
```

```bash
# Create an order (use the product id from above)
curl -X POST http://localhost:3000/api/orders \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "675853a1b2c3d4e5f6789abc",
    "product_name": "Test Laptop",
    "quantity": 2,
    "total_price": 2599.98,
    "customer_email": "test@example.com"
  }'
```

**Expected Output:**

```json
{
  "id": 1,
  "product_id": "675853a1b2c3d4e5f6789abc",
  "product_name": "Test Laptop",
  "quantity": 2,
  "total_price": "2599.98",
  "customer_email": "test@example.com",
  "status": "pending",
  "created_at": "2024-12-10T12:35:20.456Z"
}
```

```bash
# Get all orders
curl http://localhost:3000/api/orders
```

**Expected Output:**

```json
[
  {
    "id": 1,
    "product_id": "675853a1b2c3d4e5f6789abc",
    "product_name": "Test Laptop",
    "quantity": 2,
    "total_price": "2599.98",
    "customer_email": "test@example.com",
    "status": "pending",
    "created_at": "2024-12-10T12:35:20.456Z"
  }
]
```

**Kill the port-forward:**

```bash
pkill -f "port-forward svc/api-gateway"
```

---

## ✅ Step 9: Check Pod Logs (Verify No Errors)

```bash
# Check API Gateway logs
kubectl logs -l app=api-gateway --tail=20
```

**Expected Output:**

```
🚀 API Gateway running on port 3000
```

```bash
# Check Product Service logs
kubectl logs -l app=product-service --tail=20
```

**Expected Output:**

```
INFO:     Started server process [1]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

```bash
# Check Order Service logs
kubectl logs -l app=order-service --tail=20
```

**Expected Output:**

```
✅ Database initialized
🚀 Order Service running on port 3001
```

---

## ✅ Step 10: Database Connectivity Check

```bash
# Test MongoDB connection
kubectl exec -it $(kubectl get pod -l app=mongodb -o jsonpath='{.items[0].metadata.name}') -- mongosh -u admin -p password123 --eval "db.adminCommand('ping')"
```

**Expected Output:**

```
{ ok: 1 }
```

```bash
# Test PostgreSQL connection
kubectl exec -it $(kubectl get pod -l app=postgres -o jsonpath='{.items[0].metadata.name}') -- psql -U postgres -d orders_db -c "SELECT 1;"
```

**Expected Output:**

```
 ?column?
----------
        1
(1 row)
```

---

## 🚨 Troubleshooting Common Issues

### **Issue 1: Pods Not Running**

```bash
kubectl get pods
kubectl describe pod <pod-name>
```

**Look for:**

- `ImagePullBackOff` → Docker Hub credentials issue
- `CrashLoopBackOff` → Application error, check logs
- `Pending` → Resource constraints or PVC issues

### **Issue 2: Metrics Endpoint Returns 404**

```bash
# Check if the service is exposing metrics
kubectl get endpoints api-gateway-metrics
```

**Should show:**

```
NAME                  ENDPOINTS           AGE
api-gateway-metrics   10.244.x.x:3000     5m
```

### **Issue 3: Can't Connect to Services**

```bash
# Check service endpoints
kubectl get endpoints

# Test service DNS resolution from inside cluster
kubectl run curl-test --image=curlimages/curl -i --rm --restart=Never -- \
  curl -s http://api-gateway/health
```

---

## 📊 Summary Checklist

Run this complete verification script:

```bash
#!/bin/bash

echo "=== 1. Checking Pods ==="
kubectl get pods --all-namespaces
echo ""

echo "=== 2. Checking Services ==="
kubectl get svc
echo ""

echo "=== 3. Checking ServiceMonitors ==="
kubectl get servicemonitors -n monitoring
echo ""

echo "=== 4. Testing API Gateway Health ==="
kubectl port-forward svc/api-gateway 3000:80 > /dev/null 2>&1 &
PF_PID=$!
sleep 3
curl -s http://localhost:3000/health | jq .
kill $PF_PID
echo ""

echo "=== 5. Testing Metrics Endpoints ==="
kubectl port-forward svc/api-gateway 3000:80 > /dev/null 2>&1 &
PF_PID=$!
sleep 3
curl -s http://localhost:3000/metrics | head -n 5
kill $PF_PID
echo ""

echo "=== 6. Checking Pod Logs ==="
echo "API Gateway:"
kubectl logs -l app=api-gateway --tail=3
echo ""
echo "Product Service:"
kubectl logs -l app=product-service --tail=3
echo ""
echo "Order Service:"
kubectl logs -l app=order-service --tail=3

echo ""
echo "✅ Verification Complete!"
```

Save as `verify.sh`, make executable, and run:

```bash
chmod +x verify.sh
./verify.sh
```

---

**Share any errors and we'll help you debug!** 🔍
