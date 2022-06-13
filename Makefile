PACKAGE_DIR=$$(poetry version | sed 's/-/_/g' | awk '{print $$1}')
DOCKER_TAG=$$(poetry version | awk '{print $$1":"$$2}')

.PHONY: format
format:
	@poetry run isort .
	@poetry run black .

.PHONY: format-check
format-check:
	@poetry run isort --check .
	@poetry run black --check .

.PHONY: lint
lint:
	@poetry run pylint -d C,R,fixme $(PACKAGE_DIR) tests
	@poetry run mypy --show-error-codes $(PACKAGE_DIR) tests

.PHONY: test
test:
	@poetry run pytest tests
	@poetry run coverage-badge -f -o docs/img/coverage.svg

# .PHONY: lint-docker
# lint-docker:
# 	@hadolint ./Dockerfile

# .PHONY: build-docker
# build-docker:
# 	@docker build --no-cache -t $(DOCKER_TAG) .

# .PHONY: scan-docker
# scan-docker:
# 	@dockle $(DOCKER_TAG)
# 	@trivy image --ignore-unfixed $(DOCKER_TAG)

# .PHONY: scan-docker-for-actions
# scan-docker-for-actions:
# 	# -------------------- dockle -------------------- #
# 	@dockle --no-color -q $(DOCKER_TAG)
# 	# -------------------- trivy -------------------- #
# 	@trivy image --ignore-unfixed $(DOCKER_TAG)

# .PHONY: docker
# docker: lint-docker build-docker scan-docker

# TODO: add docker
.PHONY: pre-commit
pre-commit: format lint test

.PHONY: run
run:
	@poetry run streamlit run main.py
