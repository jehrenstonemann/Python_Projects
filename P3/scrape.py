# project: p3
# submitter: xhuang438
# partner: none
# hours: 8

from collections import deque
import os
import pandas as pd
from selenium.webdriver.common.by import By
import time
import requests
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class Parent:
    def twice(self):
        self.message()
        self.message()
        
    def message(self):
        print("parent says hi")
        
class Child (Parent):
    def message(self):
        print("child says hi")
        
class GraphSearcher:
    def __init__(self):
        self.visited = set()
        self.order = []

    def visit_and_get_children(self, node):
        """ Record the node value in self.order, and return its children
        param: node
        return: children of the given node
        """
        raise Exception("must be overridden in sub classes -- don't change me here!")

    def dfs_search(self, node):
        # 1. clear out visited set and order list
        self.visited.clear()
        self.order.clear()
        
        # 2. start recursive search by calling dfs_visit
        self.dfs_visit(node)

    def dfs_visit(self, node):
        if node in self.visited:
            return
        self.visited.add(node)
        children = self.visit_and_get_children(node)
        self.order.append(node)
        for child in children:
            self.dfs_visit(child)
            
    def bfs_search(self, start_node):
        self.visited.clear()
        self.order.clear()
        self.bfs_visit(start_node)
            
    def bfs_visit(self, node):
        queue = deque([node])
        while len(queue) > 0:
            priority = queue.popleft()
            if priority not in self.visited:
                self.visited.add(priority)
                self.order.append(priority)
                children = self.visit_and_get_children(priority)
                for child in children:
                    if child not in queue:
                        if child not in self.visited:
                            queue.append(child)
                    
class MatrixSearcher(GraphSearcher):
    def __init__(self, df):
        super().__init__() 
        self.df = df

    def visit_and_get_children(self, node):
        children = []
        for child, has_edge in self.df.loc[node].items():
            if has_edge:
                children.append(child)
        return children

class FileSearcher(GraphSearcher):
    def __init__(self):
        super().__init__()

    def visit_and_get_children(self, node):
        children = []
        path = "file_nodes/" + node
        with open(path, 'r') as file:
            file.readline().strip()
            children_line = file.readline().strip()
            if children_line:
                children = children_line.split(",")
        return children

    def concat_order(self):
        result = ""
        for file in self.order:
            file_path = "file_nodes/" + file
            with open(file_path,'r') as file:
                result += file.readline().strip()
        return result
    
class WebSearcher(GraphSearcher):
    def __init__(self, driver):
        super().__init__()
        self.driver = driver
        self.table_fragments = []

    def visit_and_get_children(self, url):
        self.driver.get(url)
        links = self.driver.find_elements(By.TAG_NAME, 'a')
        children = []
        for link in links:
            children.append(link.get_attribute('href'))
        self.table_fragments.append(pd.read_html(self.driver.page_source)[0])
        return children

    def table(self):
        return pd.concat(self.table_fragments, ignore_index=True)

def reveal_secrets(driver, url, travellog):
    password = ''.join(str(clue) for clue in travellog['clue'])
    driver.get(url)
    password_input = driver.find_element("id", "password-textbox") 
    password_input.send_keys(password)
    go_button = driver.find_element("id", "submit-button") 
    go_button.click()
    time.sleep(5)  
    view_location_button = driver.find_element("id", "view-location-button") 
    view_location_button.click()
    time.sleep(5)
    image_element = driver.find_element("id", 'image') 
    image_url = image_element.get_attribute('src')
    response = requests.get(image_url)
    if response.status_code == 200:
        with open('Current_Location.jpg', 'wb') as file:
            file.write(response.content)
    current_location_element = driver.find_element("id", "location")
    return current_location_element.text