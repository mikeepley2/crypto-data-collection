# Crypto Data Collection - Containerized Test Management
# No local Python environment required - everything runs in containers

.PHONY: help test test-unit test-integration test-all clean build setup

# Default target
help:
	@echo "🐳 Crypto Data Collection - Containerized Testing"
	@echo "=================================================="
	@echo ""
	@echo "Available commands:"
	@echo "  make setup         - Start test infrastructure (MySQL, Redis)"
	@echo "  make test-unit     - Run fast unit tests only"
	@echo "  make test-integration - Run comprehensive integration tests"
	@echo "  make test-all      - Run comprehensive test suite with coverage"
	@echo "  make test-all-services - Run all service integration tests"
	@echo "  make build         - Build test containers"
	@echo "  make clean         - Stop and remove all test containers"
	@echo ""
	@echo "🛡️  All tests use isolated test database - production never touched"
	@echo "🚀 Perfect for CI/CD pipelines - no local dependencies"

# Start test infrastructure
setup:
	@echo "🏗️  Starting test infrastructure..."
	docker-compose -f docker-compose.test.yml up test-mysql test-redis -d
	@echo "⏳ Waiting for services to be ready..."
	@sleep 10
	@echo "✅ Test infrastructure ready"

# Run fast unit tests (no database dependencies)
test-unit:
	@echo "⚡ Running unit tests in container..."
	./run_containerized_tests.sh unit

# Run integration tests with isolated test database  
test-integration:
	@echo "🔗 Running comprehensive integration tests in container..."
	./run_containerized_tests.sh integration

# Run comprehensive test suite with all services
test-all:
	@echo "🚀 Running comprehensive service test suite in container..."
	./run_containerized_tests.sh all

# Run all service integration tests
test-all-services:
	@echo "🏢 Running all service integration tests..."
	docker-compose -f docker-compose.test.yml up --abort-on-container-exit test-all-services

# Build test containers
build:
	@echo "🐳 Building test containers..."
	docker-compose -f docker-compose.test.yml build

# Clean up everything
clean:
	@echo "🧹 Cleaning up test containers and volumes..."
	docker-compose -f docker-compose.test.yml down -v --remove-orphans
	docker system prune -f --volumes

# Quick test for CI/CD (unit + integration)
test-ci: test-unit test-integration

# Full pipeline test (everything)
test-pipeline: build test-all clean

# Show container status
status:
	@echo "📊 Test container status:"
	docker-compose -f docker-compose.test.yml ps

# View logs
logs:
	docker-compose -f docker-compose.test.yml logs -f

# One-time setup for new environment
init: build setup
	@echo "🎉 Test environment initialized and ready!"
	@echo ""
	@echo "Next steps:"
	@echo "  make test-unit        # Quick test"
	@echo "  make test-integration # Full integration test" 
	@echo "  make test-all         # Everything"
