def bar(line, maxchar=10):
    #print 'foo'
    if len(line) <= maxchar: return line
    result = ''
    ll = 0
    #print line.split(' ')
    for token in line.split(' '):
        #print token

        if ll+len(token)+1 <= maxchar:
            result += ' '+token
            ll += len(token)+1
        else:
            result += '\n'
            ll = 0
    return result

def compare(s1, s2):
    if s1.find(s2):
        print "same"
    else:
        print "not same"


class foo:
    x = 'foo'
    def foo(self):
        def bar():
            print self.x
        for i in range(1, 3):
            print i
            bar()
    def foobar(self):
        bar()

if __name__ == '__main__':
    s = ' '.join(['x' for x in range(0, 100)])
    print bar(s)

    s = 'a string \
too long'
    print s
    

    #foo = foo()
    #foo.foo()
    #foo.bar()

    compare('foo', 'foo')
    compare('foo', 'bar')
