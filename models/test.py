
def strs(li: list):
    def str_filter(str,list_str):
        if str in list_str:
            return True
        else:
            return False
    



if __name__ == "__main__":
    list_str = ["abca","abc1","abc2"]
    strs(list_str)