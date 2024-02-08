IMAGE_NAME=sessions

# TODO: Установить Make
build:
	docker build . --file build/service/Dockerfile --tag sessions --pull --no-cache