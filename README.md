# 🎬 Videoflix Backend

Videoflix Backend is the server-side component of the Videoflix application — a video streaming platform built with Django REST Framework.
It provides all core functionalities such as user authentication, video management, and API endpoints that power the Videoflix Frontend
.

This backend was designed for Developer Akademie students to deepen their understanding of backend development, Docker-based deployment, and integration between Django APIs and a vanilla JavaScript frontend.

It serves as the main data and API layer for the frontend, managing:

User registration, login, and authentication (JWT)

Video uploads, metadata, and streaming endpoints

Background tasks via Redis & RQ

Static and media file handling

Database management with PostgreSQL

Together with the frontend project, this repository demonstrates a full-stack video streaming solution using modern web technologies and clean development practices.

Frontend Repository: [Videoflix/ Frontend Project](https://github.com/Developer-Akademie-Backendkurs/project.Videoflix)

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

Launch the Gunicorn server at http://127.0.0.1:8000
