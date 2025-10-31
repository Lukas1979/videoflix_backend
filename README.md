# 🎬 Videoflix Backend

Backend for **Videoflix**, a Django REST Framework-based project designed to handle video streaming, authentication, and background processing via Redis queues.

This repository contains everything needed to start the backend using **Docker**, including configuration for PostgreSQL and Redis.

---

## 🧩 Requirements

Before you begin, make sure you have the following installed:

- **[Docker Desktop](https://www.docker.com/products/docker-desktop/)** (latest version)  
  – includes Docker Engine and Docker Compose  
- **Git** (for cloning this repository)  
- *(Optional)* **Python 3.12+** and **pip** if you want to run Django commands locally (not required for Docker use)

> 🧠 Docker Desktop must be running before you start the containers.

---

## 🧰 Tech Stack

- **Python 3.12 (Alpine)**
- **Django REST Framework**
- **PostgreSQL 17**
- **Redis (latest)**
- **Gunicorn**
- **RQ (Redis Queue)**
- **Docker & Docker Compose**

---

## 🚀 Quick Start

### 1️⃣ Clone the repository

```bash
git clone https://github.com/yourusername/videoflix_backend.git
cd videoflix_backend
```
   
### 2️⃣ Create your environment file

Duplicate the provided template:

```bash
cp .env.template .env
```

Then open .env and fill in the required values.

  
### 3️⃣ Build and start Docker containers

If you use Docker Desktop, simply click ▶ Play on the videoflix_backend setup
—or use the terminal:

```bash
docker compose up --build
```

This will:

Build the backend image using backend.Dockerfile

Start PostgreSQL and Redis services

Wait for PostgreSQL to be ready

Run Django migrations and static file collection

Automatically create a Django superuser (from .env)

Launch the Gunicorn server at http://localhost:8000

⚙️ Available Services
Service	            Description	             Port	       Container Name
web	        Django backend (Gunicorn)	     8000	      videoflix_backend
db	         PostgreSQL 17 database	         5432	      videoflix_database
redis	    Redis cache / task queue	     6379	       videoflix_redis
