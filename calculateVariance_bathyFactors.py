import numpy as np

M = np.array([[3, 1, 1, 5], [1,1,1,1], [1, 1, 1, 1], [2, 1,1 , 4] ])

# if M is (nxn), function returns a (nxn) matrix where each point represents the variance of the original point based on 8 surrounding points
def calculateVar_pts_in_matrix(M):
    var_matrix = np.zeros((len(M[:,0]), len(M[0,:])))
    for i in range(1,len(M[:,0])-1):       #for all rows except first and last
        for j in range(1,len(M[0,:])-1):   #for all columns except first and last
            pts = np.array([ M[i,j] , M[i+1, j] , M[i+1, j-1], M[i+1,j+1], M[i,j+1], M[i, j-1], M[i-1, j], M[i-1, j+1], M[i-1, j-1]])
            var_matrix[i,j] = np.var(pts)
    #Set Equal edges to inside rows
    var_matrix[:,0] = var_matrix[:,1]
    var_matrix[:,len(M[0,:])-1] = var_matrix[:,len(M[0,:]) - 2]
    var_matrix[0,:] = var_matrix[1,:]
    var_matrix[len(M[:,0])-1, :] = var_matrix[len(M[:,0]) - 2,:]
    return(var_matrix)

test = calculateVar_pts_in_matrix(M)
print(M)
print(test)
# var_matrix = np.zeros((4,4)
# for i in range(1,len(M[:,0])-1):       #for all rows except first and last
#     for j in range(1,len(M[0,:])-1):   #for all columns except first and last
#         pts = np.array([ M[i,j] , M[i+1, j] , M[i+1, j-1], M[i+1,j+1], M[i,j+1], M[i, j-1], M[i-1, j], M[i-1, j+1], M[i-1, j-1]])
#         # print(pts)
#         var_matrix[i,j] = np.var(pts)