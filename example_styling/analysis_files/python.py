
def hello(s):
    def inner():
        for c in s:
            print(c, end="")
        print()
        return s
    return inner()

hello('Hello World!')
