from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response
import os
import time
from typing import List, Optional

app = FastAPI(title="Product Service")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics
REQUEST_COUNT = Counter('product_service_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('product_service_request_duration_seconds', 'Request duration', ['method', 'endpoint'])

# MongoDB connection
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
client = AsyncIOMotorClient(MONGO_URL)
db = client.products_db
products_collection = db.products

# Models
class Product(BaseModel):
    name: str
    description: str
    price: float
    stock: int

class ProductResponse(Product):
    id: str

# Middleware for metrics
@app.middleware("http")
async def metrics_middleware(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    REQUEST_DURATION.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)
    
    return response

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "product-service"}

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.post("/products", response_model=ProductResponse, status_code=201)
async def create_product(product: Product):
    product_dict = product.dict()
    result = await products_collection.insert_one(product_dict)
    product_dict["id"] = str(result.inserted_id)
    return product_dict

@app.get("/products", response_model=List[ProductResponse])
async def get_products():
    products = []
    async for product in products_collection.find():
        product["id"] = str(product.pop("_id"))
        products.append(product)
    return products

@app.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(product_id: str):
    from bson import ObjectId
    product = await products_collection.find_one({"_id": ObjectId(product_id)})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    product["id"] = str(product.pop("_id"))
    return product

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)