import numpy as np

#initialization
a = np.array([[1,2,3],[1,2,3]], dtype="int32")
b = np.array([1,2,3])
c = np.array([1.1,22,3.11])
d = np.array([[1,2,3,4,5,6],[1,2,3,4,5,6]])
e = np.ones((4,4))


print(a.ndim)
print(a.dtype)
print(a.nbytes)
print(a.shape)


print(a[1][:])
print(a[:][1])
print(a[1,2])
#inddex submatrix


print(d[0, 1:6:2]) #[startindex:endindex:stepsize]

d[1,5]  =20
print(d)

np.zeros(5)
np.ones((4,3,2), dtype='int32')
np.full((2,2), 10, dtype='float32')
np.full_like(a,  4) #fill array with dimensions a with 4

np.random.randint(7, size=(3,3))

arr = np.array([1,2,3])
r1=np.repeat(arr, 3, 0)

r2 = r1.copy()

a+2
a-2
a*2
a**2
a/2
np.cos(a)

before = np.array([[1,2,3,4],[1,2,3,4]])
after  = before.reshape((2,2,2))
v1 = np.array([1,2,3,4])
v2 = np.array([1,2,3,4])
np.vstack([v1,v2,v1])
np.hstack([v1,v2,v1])

# data = np.genfromtxt('file.txt', delimiter=',')
# data.astype('int32')

# #returns  boolean area of which locations are greater than 50
# data > 50
# #returns values greater than 50
# data[data > 50]


