publish:
	date +%s > tag.txt
	docker build -t ghcr.io/lawrencegripper/givenergy-automation:$$(cat tag.txt) -t ghcr.io/lawrencegripper/givenergy-automation:latest .
	docker push ghcr.io/lawrencegripper/givenergy-automation:$$(cat tag.txt)
	docker push ghcr.io/lawrencegripper/givenergy-automation:latest

deploy: publish
	kubectl apply -f ./Deployment.yaml