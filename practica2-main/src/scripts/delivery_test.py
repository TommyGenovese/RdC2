import pika
import request

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

channel.queue_declare(queue='delivery_queue', durable=True)
req = request.Request('carlos', request.productsFromString('lapiz hoja'))
req.found(request.Product('lapiz'))
req.found(request.Product('hoja'))
req.move()

channel.basic_publish(
    exchange='',
    routing_key='delivery_queue',
    body='DELIVERY ' + req.requestInfo()
)

channel.queue_declare(queue='delivery_to_x', durable=True)

def callback(channel, method, properties, body):
    msg = body.decode()
    print(f'Received: {msg}')
    channel.basic_ack(delivery_tag=method.delivery_tag)

channel.basic_consume(queue='delivery_to_x', on_message_callback=callback)
try:
    channel.start_consuming()
except:
    channel.stop_consuming()

try:
    channel.close()
except:
    pass
connection.close()