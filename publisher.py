import zmq

HOST = "127.0.0.1"
TOPIC_PORT = 5556
RPC_PORT = 5557

context = zmq.Context()

topic_socket = context.socket(zmq.PUB)
topic_socket.bind("tcp://{}:{}".format(HOST, TOPIC_PORT))

rpc_socket = context.socket(zmq.REP)
rpc_socket.bind("tcp://{}:{}".format(HOST, RPC_PORT))

topics = {}

while True:
    try:
        message = rpc_socket.recv_json(flags=zmq.NOBLOCK)
        if message["type"] == "individual":
            dest = message["to"]
            msg = message["message"]
            topic_socket.send_multipart([dest.encode("utf-8"), msg.encode("utf-8")])
            rpc_socket.send_json({"status": "ok"})
        elif message["type"] == "topic":
            topic = message["topic"]
            msg = message["message"]
            topic_socket.send_multipart([topic.encode("utf-8"), msg.encode("utf-8")])
            rpc_socket.send_json({"status": "ok"})
    except zmq.Again:
        pass

    try:
        topic, message = topic_socket.recv_multipart()
        if topic in topics:
            for subscriber in topics[topic]:
                topic_socket.send_multipart([subscriber.encode("utf-8"), message])
    except zmq.Again:
        pass

    try:
        conn = rpc_socket.recv(flags=zmq.NOBLOCK)
        rpc_socket.send_json({"status": "ok"})
    except zmq.Again:
        pass

    try:
        topic, subscriber = topic_socket.recv_multipart(flags=zmq.NOBLOCK)
        if topic not in topics:
            topics[topic] = set()
        topics[topic].add(subscriber.decode("utf-8"))
    except zmq.Again:
        pass
