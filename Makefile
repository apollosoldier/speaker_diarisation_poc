






psql:
	docker exec -it speakerdiarisationpoc_db_1 sh -c 'psql -U postgres speaker_diarisation'

web:
	docker exec -it speakerdiarisationpoc_web_1 bash

deploy_web:
	docker-compose up --build --force-recreate -d web

kafka_consumer:
	docker exec -it speakerdiarisationpoc_kafka_1 sh -c '/opt/kafka/bin/kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic foobar --from-beginning'

kafka_producer:
	docker exec -it speakerdiarisationpoc_kafka_1 sh -c '/opt/kafka/bin/kafka-console-producer.sh --broker-list localhost:9092 --topic foobar'
