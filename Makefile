IMAGE_NAME=sessions

build:
	docker build . --platform linux/amd64 --file build/service/Dockerfile --tag sessions --pull --no-cache
.PHONY: build

save:
	docker save -o sessions.tar sessions

