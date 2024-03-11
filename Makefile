publish:
	echo "v0.1.$$(date +%s)" > tag.txt
	docker build -t ghcr.io/lawrencegripper/givenergy-automation:$$(cat tag.txt) -t ghcr.io/lawrencegripper/givenergy-automation:latest -t ghcr.io/lawrencegripper/givenergy-automation:v0.1 .
	docker push ghcr.io/lawrencegripper/givenergy-automation:$$(cat tag.txt)
	docker push ghcr.io/lawrencegripper/givenergy-automation:latest
	docker push ghcr.io/lawrencegripper/givenergy-automation:v0.1

deploy: publish
	kubectl apply -f ./Deployment.yaml

test-givenergy-cron:
	kubectl --namespace givenergy delete job test-set-charge || true
	kubectl --namespace givenergy create job --from=cronjob/set-charge test-set-charge