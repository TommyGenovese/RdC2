import pika

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

channel.queue_declare(queue='Move', durable=True)

# Lista de test con (req_id, [lista de productos])
requests = [
    ("1001", ["ProductoA", "ProductoB", "ProductoC"]),
    ("1002", ["ProductoX", "ProductoY"]),
    ("1003", ["ProductoZ"]),
]

for req_id, products in requests:
    message = f"Move {req_id} " + " ".join(products)
    channel.basic_publish(
        exchange='',
        routing_key='Move',
        body=message,
        properties=pika.BasicProperties(delivery_mode=2)
    )
    print(f" [>] Enviado: {message}")

connection.close()
