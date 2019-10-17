import numpy as np
import matplotlib.pyplot as plt
from abel.tools import polar
from scipy.special import eval_legendre, hyp2f1
from math import factorial
from time import time

class Abel_object():
    def __init__(self, data, center_x, center_y, d_alpha_deg, dr, N, parent=None):
        """
            Creates an object that can Abel invert an image using the DAVIS
            (Direct Algorithm for Velocity-map Imaging) technique described in
            https://doi.org/10.1063/1.5025057

            Parameters
            ----------
            data : 2D np.array
                The data to invert
            center_x : int
                x coordinate of the center of the image, corresponds to vertical axis
                if the data is transposed
            center_y : int
                y coordinate of the center of the image
            d_alpha_deg : float
                Angular coordinate spacing (in degrees)
            dr : int
                Radial coordinate spacing for the inverted array
            N : int
                number of photons. Determines the number of legendre polynomials
                to use (which is equal to 2N+1)
                ex: if N=1 then P0, P1 and P2 are used, if N=2 then P0 to P4 are used.
        """

        self.parent = parent

        self.center_x = center_x
        self.center_y = center_y
        self.d_alpha = d_alpha_deg * np.pi / 180  # deg to rad conversion
        self.dr = dr
        self.N = N

        self.Ny, self.Nx = data.shape

        self.N_alpha = int(2 * np.pi / self.d_alpha)
        self.N_R = int(min((self.Ny - center_y) / dr, (self.Nx - center_x) / dr))

        self.R_vector = np.linspace(dr, self.N_R * dr, self.N_R)
        self.alpha_vector = np.linspace(2 * np.pi / self.N_alpha, 2 * np.pi, self.N_alpha)

        self.data_polar, r_grid, theta_grid = polar.reproject_image_into_polar(
            data, origin=(center_x, center_y), dr=dr, dt=self.d_alpha, Jacobian=True)

        self.M_inv = {}
        self.Mnk = {}
        self.F = {}

    def set_data(self, data):
        if data.shape != (self.Ny, self.Nx):
            print('Incorrect data shape')
            raise ValueError
        self.data_polar, r_grid, theta_grid = polar.reproject_image_into_polar(
            data, origin=(self.center_x, self.center_y), dr=self.dr, dt=self.d_alpha, Jacobian=True)

    def show(self, data):
        plt.figure()
        g = plt.pcolormesh(data.T)
        plt.colorbar(g)
        plt.show()

    def cart2pol(self, x, y):
        rho = np.sqrt(x**2 + y**2)
        phi = np.arctan2(y, x)
        return(rho, phi)

    def falling_factorial(self, x, m):
        prod = 1
        for i in range(int(m)):
            prod *= (x-i)
        return prod

    def summand_cnkl(self, n,k,l,p):
        ''' this function is used by the c function'''
        return self.falling_factorial(2*(n-2*k+l-p),2*(l-p))/\
                    self.falling_factorial(2*(l-p),2*(l-p))*self.c(n,k-l+p,p)

    def c(self, n,k,l):
        ''' This function is defined in eqn. 7 and used in the Gamma function
         to calculate the transformation matrices Mn,n-2k'''
        c = self.falling_factorial(n-k+l-1/2,k-l)*self.falling_factorial(n-k,l)*\
            self.falling_factorial(n-2*k+2*l-1/2,2*l)/(self.falling_factorial(2*l,2*l)*\
                                                       self.falling_factorial(n-k+l-1/2,l))
        if l>0:
            c = c - 1/(2**(k+l))*np.array([self.summand_cnkl(n,k,l,p) for p in range(0,l)]).sum()
        return c

    def Gammma(self,n,k,l,i,ip):
        ''' This function is defined in eqn. 11 and used to calculate the transformation matrices Mn,n-2k '''
        if ip==i:
            R_plus = self.R_vector[i] # this is a trick of mine, otherwise R_plus/R_vector[ip] > 1
            # and the hypergeometric function in eqn. 11 is not defined
        else:
            R_plus = self.R_vector[i] + dr/2
        R_minus = self.R_vector[i] - dr / 2
        try:
            return 1/(2+2*l-2*k+n)*\
                  (((R_plus)/self.R_vector[ip])**(2+2*l-2*k+n)*\
                   hyp2f1(1/2+l-k,1+l-k+n/2,2+l-k+n/2,(R_plus/self.R_vector[ip])**2)\
                - ((R_minus)/self.R_vector[ip])**(2+2*l-2*k+n)*\
                   hyp2f1(1/2+l-k,1+l-k+n/2,2+l-k+n/2,(R_minus/self.R_vector[ip])**2))
                # I replaced R_vector[i]+dr/2 by R_vector[i]
        except ZeroDivisionError:
            print('ZeroDivisionError in Gamma function')

    def M_eq13(self,N_R, n, k): # from equation 13
        ''' This function calculates the upper triangular transformation matrices Mn,n-2k using the formula of eqn. 13
        It uses the functions Gamma and c. It is not currently used but I thought it could be useful for n>4'''
        sM = np.zeros((N_R,N_R))
        for i in range (0, N_R):
            for ip in range(i, N_R):
                    sM[i,ip] = np.array([(-1)**(k-l)*2**(2*l+1)/factorial(k-l)*self.c(n,k,l)*self.dr*self.d_alpha* \
                                         self.Gammma(n,k,l,i,ip) for l in range(0,max(k-1,0)+1)]).sum()
        return sM

    def M(self,N_R,n,k):
        ''' This function calculates the upper triangular transformation matrices Mn,n-2k using the analytical formulas
        from Table I. I checked that it's equal to M_eqn13(N_R,n,k). However it's faster than M_eq13 so this is the function
        actually used '''
        d_alpha = self.d_alpha
        dr = self.dr
        M = np.zeros((N_R,N_R))
        for i in range (0, N_R):
            for ip in range(i, N_R):
                if ip == i:
                    R_plus = self.R_vector[i]
                else:
                    R_plus = self.R_vector[i] + dr/2 # Ri ^ = Ri + DeltaR/2
                R_minus = self.R_vector[i] - dr/2 # Ri v = Ri - DeltaR/2
                R_ip = self.R_vector[ip] # ri'

                if(n==0 and k==0): # M00
                    M[i,ip] = 2*dr*d_alpha/R_ip*(np.sqrt(R_ip**2-R_minus**2)-np.sqrt(R_ip**2-R_plus**2))
                elif(n==1 and k==0): # M11
                    M[i,ip] = dr*d_alpha/R_ip**2*\
                              (R_minus*np.sqrt(R_ip**2-R_minus**2)-R_plus*np.sqrt(R_ip**2-R_plus**2)+\
                               R_ip**2*np.arcsin(R_plus/R_ip)-R_ip**2*np.arcsin(R_minus/R_ip))
                elif(n==2 and k==0): # M22
                    M[i,ip] = 2*dr*d_alpha/(3*R_ip**3)*\
                              (np.sqrt(R_ip**2-R_minus**2)*(2*R_ip**2+R_minus**2)-\
                               np.sqrt(R_ip**2-R_plus**2)*(2*R_ip**2+R_plus**2))
                elif(n==2 and k==1): # M20
                    M[i,ip] = dr*d_alpha/(3*R_ip**3)*((R_ip**2-R_plus**2)**(3/2)-(R_ip**2-R_minus**2)**(3/2))
                elif(n==3 and k==0): # M33
                    M[i,ip] = dr*d_alpha/(4*R_ip**4)*\
                              (R_minus*np.sqrt(R_ip**2-R_minus**2)*(3*R_ip**2+2*R_minus**2)-\
                               R_plus*np.sqrt(R_ip**2-R_plus**2)*(3*R_ip**2+2*R_plus**2)+\
                               3*R_ip**4*np.arcsin(R_plus/R_ip) - 3*R_ip**4*np.arcsin(R_minus/R_ip))
                elif(n==3 and k==1): # M31
                    M[i,ip] = 3*dr*d_alpha/(8*R_ip**4)*\
                              (R_minus*np.sqrt(R_ip**2-R_minus**2)*((-1)*R_ip**2+2*R_minus**2)-\
                               R_plus*np.sqrt(R_ip**2-R_plus**2)*((-1)*R_ip**2+2*R_plus**2)+\
                               R_ip**4*np.arcsin(R_minus/R_ip) - R_ip**4*np.arcsin(R_plus/R_ip))
                elif(n==4 and k==0): # M44
                    M[i,ip] = 2*dr*d_alpha/(15*R_ip**5)*\
                              (np.sqrt(R_ip**2-R_minus**2)*(8*R_ip**4+4*R_ip**2*R_minus**2+3*R_minus**4)- \
                               np.sqrt(R_ip**2-R_plus**2)*(8*R_ip**4+4*R_ip**2*R_plus**2+3*R_plus**4))
                elif(n==4 and k==1): # M42
                    M[i,ip] = dr*d_alpha/(3*R_ip**5)*\
                              ((R_ip**2-R_plus**2)**(3/2)*(2*R_ip**2+3*R_plus**2)- \
                               (R_ip**2-R_minus**2)**(3/2)*(2*R_ip**2+3*R_minus**2))
                elif(n==4 and k==2): # M40
                    M[i,ip] = dr*d_alpha/(60*R_ip**5)*\
                              ((R_ip**2-R_plus**2)**(3/2)*((19)*R_ip**2+51*R_plus**2)- \
                               (R_ip**2-R_minus**2)**(3/2)*((19)*R_ip**2+51*R_minus**2))
                    # there is possibly an error in the paper (for M40).
                    # This corrected formula gives the same thing as M_eq13
                elif(n==6 and k==2): # M62 (not in the article)
                    M[i,ip] = dr*d_alpha/(84*R_ip**7)*\
                              ((R_ip**2-R_plus**2)**(3/2)*(975*R_plus**4+633*R_plus**2*R_ip**2+422*R_ip**4)- \
                               (R_ip**2-R_minus**2)**(3/2)*(975*R_minus**4+633*R_minus**2*R_ip**2+422*R_ip**4))
                elif(n==6 and k==3): # M60 (not in the article)
                    M[i,ip] = dr*d_alpha/(1680*R_ip**7)*\
                              ((R_ip**2-R_plus**2)**(3/2)*(2670*R_plus**4-1329*R_plus**2*R_ip**2-536*R_ip**4)- \
                               (R_ip**2-R_minus**2)**(3/2)*(2670*R_minus**4-1329*R_minus**2*R_ip**2-536*R_ip**4))
        return M

    def precalculate(self):
        N = self.N
        print('precalculating matrices...')
        for k in range(0, 2 * N + 1):
            self.M_inv[k] = np.linalg.inv(self.M(self.N_R,k,0))  # inverse of M_kk
            try:
                self.parent.progress_precalc.setValue(int((k+1)/(2*N+1)*50))
                self.parent.progress_precalc.repaint()
            except AttributeError:
                print(int((k+1)/(2*N+1)*50), " %")

        for k in range(2 * N, -1, -1):  # reversed loop from 2N to 0 included
            if k % 2 == 0:  # even k
                if k == 2 * N:  # no sum over i
                    pass
                elif k == 2 * N - 2:  # only one term in the sum
                    i = 1
                    self.Mnk[(k + 2 * i, i)] = self.M(self.N_R, k+2*i, i)
                else:
                    for i in range(1, N - k // 2 + 1):
                        self.Mnk[(k + 2 * i, i)] = self.M(self.N_R,k+2*i,i)
            elif k % 2 == 1:  # odd k
                for i in range(1, N - (int(k / 2) + 1) + 1):
                    self.Mnk[(k + 2 * i, i)] = self.M(self.N_R,k+2*i,i)
            try:
                self.parent.progress_precalc.setValue(int((2*N+1-k)/(2*N+1)*50+50))
                self.parent.progress_precalc.repaint()
            except AttributeError:
                print(int((2*N+1-k)/(2*N+1)*50+50), " %")
        print('precalculation done')

    def invert(self):
        N = self.N
        delta = np.zeros([2 * N + 1, self.N_R])
        for k in range(0, 2 * N + 1):
            for Ri in range(0, self.N_R):
                delta[k, Ri] = (2 * k + 1) / 2 * \
                        np.trapz(np.abs(np.sin(self.alpha_vector))*\
                        eval_legendre(k, np.cos(self.alpha_vector))*\
                        self.data_polar[Ri, :],dx=self.d_alpha) * 0.5
                        # I added the 0.5 because we integrate between 0 and 2pi
                        # instead of between 0 and pi

        # Application of eqn. 19
        for k in range(2 * N, -1, -1):  # reversed loop from 2N to 0 included
            if k % 2 == 0:  # even k
                if k == 2 * N:  # no sum over i
                    m2 = delta[k]
                elif k == 2 * N - 2:  # only one term in the sum
                    i = 1
                    m2 = delta[k] - np.dot(self.Mnk[(k + 2 * i, i)], self.F[k + 2 * i])
                else:
                    m2 = delta[k] - np.array(
                        [np.dot(self.Mnk[(k + 2 * i, i)], self.F[k + 2 * i]) \
                         for i in range(1, N - k // 2 + 1)]).sum(axis=0)
                self.F[k] = np.dot(self.M_inv[k], m2)
            elif k % 2 == 1:  # odd k
                m2 = delta[k] - np.array(
                    [np.dot(self.Mnk[(k + 2 * i, i)], self.F[k + 2 * i]) \
                     for i in range(1, N - (int(k / 2) + 1) + 1)]).sum(axis=0)
                self.F[k] = np.dot(self.M_inv[k], m2)


if __name__ == '__main__':

    data = np.load("5000_3945_25cm_r0p1_l3_x45_y0_z0_0deg_1eV_iso_180k_merged.npy")
    data = np.transpose(data)


    ############# INPUT PARAMETERS ##########################################
    center_x = 1024 # vertical axis if the data is transposed
    center_y = 1024
    d_alpha_deg = 1 # increment in angle alpha (in degrees)
    dr = 1 # increment in radius r
    N = 1 # number of photons. Determines the number of legendre polynomials to use (which is equal to 2N+1)
    # ex: if N=1 then P0, P1 and P2 are used. If N=2 then P0 to P4 are used.
    #########################################################################

    abel_obj = Abel_object(data, center_x, center_y, d_alpha_deg, dr, N)
    abel_obj.show(data)
    abel_obj.precalculate()
    t0 = time()
    abel_obj.invert()
    print(time()-t0)

    #for j in range(1, 2*N+1,2): # only odd j
    """for j in range(1, 2*N+1,2):
        F[j] = F[j]/F[0] # beta_j"""


    fig = plt.figure(num=None, figsize=(9, 4.5), dpi=100, tight_layout=True)
    ax = plt.subplot(1,1,1)

    for tick in ax.xaxis.get_major_ticks():
        tick.label.set_fontsize(12)
    for tick in ax.yaxis.get_major_ticks():
        tick.label.set_fontsize(12)
    ax.set_xlabel("Rayon (pixel)", fontsize=14)
    ax.set_ylabel("Intensité (u. arb.)", fontsize=14)
    ax.plot(abel_obj.F[0], label=r'$\beta_0$')
    ax.plot(abel_obj.F[1], label='norm_P1')
    ax.plot(abel_obj.F[2], label=r'$\beta_2$')
    #ax.plot(abel_obj.F[3], label=r'$\beta_3$')
    #ax.plot(abel_obj.F[4], label=r'$\beta_4$')
    plt.legend()