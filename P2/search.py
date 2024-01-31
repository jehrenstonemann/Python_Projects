class Node():
    def __init__(self, key):
        self.key = key
        self.values = []
        self.left = None
        self.right = None
    def __len__(self):
        size = len(self.values)
        if self.left != None:
            size += len(self.left)
        if self.right:
            size += len(self.right)
        return size
    def lookup(self, key):
        # If the key matches, return my values
        if key == self.key:
            return self.values
        result = []
        # If key is less than my key and I have a left child
        if key < self.key and self.left:
            result += self.left.lookup(key)
        # If key is greater than my key and I have a right child
        if key > self.key and self.right:
            result += self.right.lookup(key)
        return result
    
class BST():
    def __init__(self):
        self.root = None

    def add(self, key, val):
        if self.root == None:
            self.root = Node(key)
        curr = self.root
        while True:
            if key < curr.key:
                # go left
                if curr.left == None:
                    curr.left = Node(key)
                curr = curr.left
            elif key > curr.key:
                # go right
                if curr.right == None:
                    curr.right = Node(key)
                curr = curr.right
            else:
                # found it!
                assert curr.key == key
                break

        curr.values.append(val)
    def __dump(self, node):
        if node == None:
            return
        self.__dump(node.right)            
        print(node.key, ":", node.values)  
        self.__dump(node.left)             

    def dump(self):
        self.__dump(self.root)
        
    def __getitem__(self,key):
        return self.root.lookup(key)
    