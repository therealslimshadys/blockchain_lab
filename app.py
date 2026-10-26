import hashlib
import json
import time


class Block:
    def __init__(self, index, timestamp, data, previous_hash, creator="unknown", nonce=0):
        self.index = index
        self.timestamp = timestamp
        self.data = data
        self.previous_hash = previous_hash
        self.creator = creator
        self.nonce = nonce
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        # Хеш включает nonce для механизма PoW
        s = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "data": self.data,
            "previous_hash": self.previous_hash,
            "creator": self.creator,
            "nonce": self.nonce,
        }, sort_keys=True).encode()
        return hashlib.sha256(s).hexdigest()

    def mine_block(self, difficulty):
        # Поиск nonce, при котором хеш начинается с difficulty нулей
        target = '0' * difficulty
        start = time.time()
        attempts = 0
        while not self.hash.startswith(target):
            self.nonce += 1
            self.hash = self.calculate_hash()
            attempts += 1
        elapsed = time.time() - start
        print(f"    Блок #{self.index} смайнен за {elapsed:.2f} сек. "
              f"(попыток: {attempts}, nonce: {self.nonce})")
        return self.hash

    def to_dict(self):
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "data": self.data,
            "previous_hash": self.previous_hash,
            "creator": self.creator,
            "nonce": self.nonce,
            "hash": self.hash,
        }

    @staticmethod
    def from_dict(d):
        b = Block(d["index"], d["timestamp"], d["data"],
                  d["previous_hash"], d.get("creator", "unknown"),
                  d.get("nonce", 0))
        b.hash = d["hash"]
        return b


class Blockchain:
    def __init__(self, difficulty=4):
        self.difficulty = difficulty
        # Генезис-блок также проходит PoW
        genesis = Block(0, time.time(), "Genesis", "0", "system")
        genesis.mine_block(self.difficulty)
        self.chain = [genesis]

    def get_latest_block(self):
        return self.chain[-1]

    def add_block(self, data, creator="unknown"):
        prev = self.get_latest_block()
        block = Block(prev.index + 1, time.time(), data, prev.hash, creator)
        print(f"  [{creator}] майнинг блока #{block.index}...")
        block.mine_block(self.difficulty)
        self.chain.append(block)
        return block

    def add_block_without_validation(self, block):
        self.chain.append(block)

    def is_valid(self):
        target = '0' * self.difficulty
        for i in range(1, len(self.chain)):
            cur, prev = self.chain[i], self.chain[i - 1]
            if cur.hash != cur.calculate_hash():
                return False
            if cur.previous_hash != prev.hash:
                return False
            if not cur.hash.startswith(target):
                return False
        return True

    def is_block_valid(self, block):
        target = '0' * self.difficulty
        if block.hash != block.calculate_hash():
            return False
        if block.previous_hash != self.get_latest_block().hash:
            return False
        if not block.hash.startswith(target):
            return False
        return True

    def has_block_at_index(self, index):
        return any(b.index == index for b in self.chain)


class Node:
    def __init__(self, node_id, difficulty=4):
        self.node_id = node_id
        self.blockchain = Blockchain(difficulty=difficulty)
        self.peers = []
        self.incoming_queue = []

    def add_peer(self, peer):
        if peer not in self.peers and peer is not self:
            self.peers.append(peer)

    def broadcast_block(self, block):
        for peer in self.peers:
            simulate_network_delivery(self, peer, block)

    def receive_block(self, block):
        if block.index != len(self.blockchain.chain):
            print(f"  [{self.node_id}] отклонён: неверный индекс")
            return False
        if not self.blockchain.is_block_valid(block):
            print(f"  [{self.node_id}] отклонён: невалидный хеш или PoW")
            return False
        if self.blockchain.has_block_at_index(block.index):
            print(f"  [{self.node_id}] отклонён: блок уже существует")
            return False

        self.blockchain.add_block_without_validation(block)
        print(f"  [{self.node_id}] принят блок #{block.index} ({block.data!r})")
        self.broadcast_block(block)
        return True

    def process_all_messages(self):
        while self.incoming_queue:
            self.receive_block(self.incoming_queue.pop(0))

    def create_and_broadcast_block(self, data):
        print(f"\n[{self.node_id}] создание и майнинг блока: {data!r}")
        block = self.blockchain.add_block(data, creator=self.node_id)
        self.broadcast_block(block)
        return block

    def print_chain(self):
        print(f"  [{self.node_id}] цепочка: {[b.data for b in self.blockchain.chain]}")


def simulate_network_delivery(sender, receiver, block):
    receiver.incoming_queue.append(Block.from_dict(block.to_dict()))


if __name__ == "__main__":
    print("=" * 60)
    print("ЛАБОРАТОРНАЯ 4: PROOF-OF-WORK")
    print("=" * 60)

    DIFFICULTY = 4

    print(f"\nСложность = {DIFFICULTY}. Инициализация узлов...")
    
    node1 = Node("Node_1", DIFFICULTY)
    node2 = Node("Node_2", DIFFICULTY)
    node3 = Node("Node_3", DIFFICULTY)

    node1.add_peer(node2); node1.add_peer(node3)
    node2.add_peer(node1); node2.add_peer(node3)
    node3.add_peer(node1); node3.add_peer(node2)

    print("\n=== Старт ===")
    for n in (node1, node2, node3):
        n.print_chain()

    print("\n" + "=" * 60)
    print("СИМУЛЯЦИЯ ОДНОВРЕМЕННОГО МАЙНИНГА")
    print("=" * 60)

    print("\n--- Node_1 майнит блок (Транзакция А) ---")
    node1.create_and_broadcast_block("Транзакция А")

    print("\n--- Node_2 майнит блок (Транзакция В) ---")
    node2.create_and_broadcast_block("Транзакция В")

    print("\n" + "=" * 60)
    print("ДОСТАВКА И ОБРАБОТКА")
    print("=" * 60)
    
    node2.process_all_messages()
    node3.process_all_messages()
    node1.process_all_messages()

    print("\n=== Итоговое состояние ===")
    for n in (node1, node2, node3):
        n.print_chain()
        print(f"  Валидность: {n.blockchain.is_valid()}")

    print("\n" + "=" * 60)
    print("ПРОВЕРКА ЗАЩИТЫ ОТ ПОДДЕЛКИ")
    print("=" * 60)
    
    print("\n1. Изменение данных в блоке #1 у Node_1")
    for b in node1.blockchain.chain:
        if b.index == 1:
            b.data = "ВЗЛОМ! Перевод всех средств"
            break
            
    print("2. Проверка is_valid() без пересчета хеша")
    print(f"  [{node1.node_id}] Валидность: {node1.blockchain.is_valid()}")

    print("\n3. Пересчет хеша без майнинга")
    for b in node1.blockchain.chain:
        if b.index == 1:
            b.hash = b.calculate_hash()
            break
            
    print(f"  [{node1.node_id}] Валидность: {node1.blockchain.is_valid()}")
    print("  (PoW нарушен, так как хеш не начинается с нужного числа нулей)")

    print("\n4. Повторный майнинг измененного блока")
    for b in node1.blockchain.chain:
        if b.index == 1:
            b.mine_block(DIFFICULTY)
            break
            
    print(f"  [{node1.node_id}] Валидность: {node1.blockchain.is_valid()}")