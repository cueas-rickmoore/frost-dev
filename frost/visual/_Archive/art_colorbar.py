import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

##  These are just for my test case=09
cmap = ListedColormap(['green','red','blue','yellow'])
contour_bounds=[-19,-13,-7,-1,5]
##  These are just for my test case=09

fg1 = map.contourf(x_new,y_new,map_val_i,clevs,cmap=cmap)
ax1 = fig.add_axes([0.25, 0.06, 0.5, 0.03])   # [left, bottom, width, height]

cbar = plt.colorbar(fg1,cax=ax1, orientation='horizontal')
cbar.ax.get_xaxis().set_ticks([])
for j,lab in enumerate(['green','red','blue','yellow']):
    print j,lab,'j lab'
    if j == 0:
        cbar.ax.text((2*j+1)/8.,0.4, lab,va='center',color='white',fontsize=8)
        cbar.ax.text((2*j+1)/8.,0.8, 'half-inch',va='center',color='white',fontsize=8)
    elif j<3:
        cbar.ax.text((2*j+1)/8.,0.5, lab,va='center',color='white')
    else:
        cbar.ax.text((2*j+1)/8.,0.5, lab,ha='center',va='center',color='black')
