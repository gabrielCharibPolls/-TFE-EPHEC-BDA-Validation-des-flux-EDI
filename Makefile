# TFE Scabel — raccourcis (natif + Docker + Railway)
.PHONY: setup init-db run test views backfill-order-facts docker-build docker-up docker-run docker-down db-reset db-push-railway simulate simulate-day figures-preview figures-drawio verify-demo

setup:
	./scripts/setup-native.sh

init-db:
	./scripts/init-db.sh

run:
	./scripts/run-validator.sh

test:
	cd validator && . .venv/bin/activate && pip install -q -r requirements.txt && python -m pytest tests/ -v

figures-preview:
	cd validator && . .venv/bin/activate && pip install -q matplotlib && python ../scripts/generate_figure_previews.py

figures-drawio:
	chmod +x scripts/export_drawio_figures.sh && ./scripts/export_drawio_figures.sh || make figures-preview

views:
	./scripts/apply-views.sh

backfill-order-facts:
	cd validator && . .venv/bin/activate 2>/dev/null; python ../scripts/backfill-order-facts.py

docker-build:
	docker compose build validator

docker-up:
	docker compose up -d db

docker-run:
	./scripts/run-docker.sh

docker-down:
	docker compose down

db-reset:
	./scripts/reset-db.sh

db-push-railway:
	./scripts/push-db-to-railway.sh

simulate:
	./scripts/run-simulator.sh

simulate-day:
	SIM_BATCH_COUNT=100 ./scripts/run-simulator.sh

verify-demo:
	chmod +x scripts/verify_demo.sh && ./scripts/verify_demo.sh

simulate-300:
	SIM_DAILY_QUOTA=300 SIM_BATCH_COUNT=300 ./scripts/run-simulator.sh
