#!/bin/bash

# Production Deployment Script for Face Recognition Attendance System

set -e

echo "========================================="
echo "Face Recognition System - Deployment"
echo "========================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Please run as root (use sudo)${NC}"
    exit 1
fi

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Install Docker if not present
if ! command_exists docker; then
    echo -e "${YELLOW}Installing Docker...${NC}"
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    echo -e "${GREEN}Docker installed successfully${NC}"
else
    echo -e "${GREEN}Docker already installed${NC}"
fi

# Install Docker Compose if not present
if ! command_exists docker-compose; then
    echo -e "${YELLOW}Installing Docker Compose...${NC}"
    apt-get update
    apt-get install -y docker-compose-plugin
    echo -e "${GREEN}Docker Compose installed successfully${NC}"
else
    echo -e "${GREEN}Docker Compose already installed${NC}"
fi

# Create .env if it doesn't exist
if [ ! -f .env ]; then
    echo -e "${YELLOW}Creating .env file...${NC}"
    cp .env.example .env
    
    # Generate random secret key
    SECRET_KEY=$(openssl rand -hex 32)
    sed -i "s/SECRET_KEY=.*/SECRET_KEY=$SECRET_KEY/" .env
    
    echo -e "${GREEN}.env file created${NC}"
    echo -e "${YELLOW}Please edit .env file with your production settings${NC}"
    
    read -p "Press enter to continue after editing .env..."
fi

# Create SSL directory
mkdir -p ssl

# Ask about SSL certificate
echo -e "${YELLOW}Do you want to set up SSL with Let's Encrypt? (y/n)${NC}"
read -r setup_ssl

if [ "$setup_ssl" = "y" ]; then
    # Install Certbot
    if ! command_exists certbot; then
        echo -e "${YELLOW}Installing Certbot...${NC}"
        apt-get update
        apt-get install -y certbot
    fi
    
    echo "Enter your domain name:"
    read -r domain
    
    echo -e "${YELLOW}Obtaining SSL certificate...${NC}"
    certbot certonly --standalone -d "$domain"
    
    # Copy certificates
    cp "/etc/letsencrypt/live/$domain/fullchain.pem" ssl/
    cp "/etc/letsencrypt/live/$domain/privkey.pem" ssl/
    
    echo -e "${GREEN}SSL certificates obtained${NC}"
    echo -e "${YELLOW}Make sure to uncomment HTTPS section in nginx.conf${NC}"
fi

# Pull latest code (if git repo)
if [ -d .git ]; then
    echo -e "${YELLOW}Pulling latest code...${NC}"
    git pull origin master
fi

# Build Docker images
echo -e "${YELLOW}Building Docker images...${NC}"
docker-compose build

# Stop existing containers
echo -e "${YELLOW}Stopping existing containers...${NC}"
docker-compose down

# Start services
echo -e "${YELLOW}Starting services...${NC}"
docker-compose up -d

# Wait for services to be healthy
echo -e "${YELLOW}Waiting for services to start...${NC}"
sleep 10

# Check service status
echo -e "\n${YELLOW}Service Status:${NC}"
docker-compose ps

# Run health check
echo -e "\n${YELLOW}Running health check...${NC}"
sleep 5
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Application is healthy${NC}"
else
    echo -e "${RED}✗ Application health check failed${NC}"
    echo "Check logs with: docker-compose logs app"
fi

echo -e "\n========================================="
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "========================================="
echo -e "API Documentation: http://localhost/api/docs"
echo -e "Health Check: http://localhost/health"
echo -e "\nUseful commands:"
echo -e "  View logs: ${YELLOW}docker-compose logs -f${NC}"
echo -e "  Stop services: ${YELLOW}docker-compose down${NC}"
echo -e "  Restart services: ${YELLOW}docker-compose restart${NC}"
echo -e "========================================="
