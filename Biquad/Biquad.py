import numpy as np
import matplotlib.pyplot as plt

class Biquad:
    def __init__(self, A=0, B=1, P=0, theta=np.pi):
        ##Setting the parameters from initialisation
        self._A = A
        self._B = B
        self._P = P
        self._theta = theta
        self.M = 8

        ##Setting up the coefficients
        self._Xn = np.zeros(self.M)
        
        self._C0 = 0 
        self._C1 = 0
        self._C2 = 0
        self._C3 = 0
        
        self._Dff = 0
        self._Dfg = 0
        self._Egg = 0
        self._Egf = 0
        
        self._a1 = 0
        self._a2 = 0

        self._update_coefficients()

####################
## Set Parameter methods
#################### 
    @property
    def A(self):
        return self._A

    @A.setter
    def A(self, value):
        if abs(value) > 8:
            raise ValueError("A must be 4 within bits wide")
        self._A = value

    @property
    def B(self):
        return self._B

    @B.setter
    def B(self, value):
        if abs(value) > 8:
            raise ValueError("B must be 4 within bits wide")
        self._B = value

    @property
    def P(self):
        return self._P

    @P.setter
    def P(self, value):
        if value > 1:
            raise ValueError("P must be less than 1")
        if value < 0:
            raise ValueError("P must be positive")
        self._P = value

    ## theta is the pole in radians
    @property
    def theta(self):
        return self._theta

    @theta.setter
    def theta(self, value):
        if value < 0 or value > np.pi:
            raise ValueError("Radians must be within semi-circle")
        self._theta = value

    def update_params(self, A, B, P, theta):
        self.A = A
        self.B = B
        self.P = P
        self.theta = theta

        self._update_coefficients()

    ###########################################
    ##### Coefficients
    ###########################################

    ##############
    ##### First FIR Pole
    ##############

    @property
    def Xn(self):
        return self._Xn

    @Xn.setter
    def Xn(self, value):
        if isinstance(value, (np.ndarray, list)) and len(value) == self.M:
            self._Xn = np.array(value)
        else:
            raise ValueError(f"Xn must be an array or list of length {self.M}")

    def _update_Xn(self):
        for n in range(self.M):
            self._Xn[n] = self.P**n * self.calc_chebyshev(n)

    ##############
    ##### Second FIR Pole
    ##############

    @property
    def Dff(self):
        return self._Dff
    
    @Dff.setter
    def Dff(self, value):
        self._Dff = value

    @property
    def Dfg(self):
        return self._Dfg
    
    @Dfg.setter
    def Dfg(self, value):
        self._Dfg = value
    
    @property
    def Egg(self):
        return self._Egg
    
    @Egg.setter
    def Egg(self, value):
        self._Egg = value

    @property
    def Egf(self):
        return self._Egf
    
    @Egf.setter
    def Egf(self, value):
        self._Egf = value

    def _update_fir(self):
        eta = self.P**7 / np.sin(self.theta)
        self._Dff = -1 * eta * self.P * np.sin(7 * self.theta)
        self._Egg = eta * self.P * np.sin(9 * self.theta)
        self._Dfg = eta * np.sin(8 * self.theta)
        self._Egf = -1 * self.P**2 * self.Dfg

    ##############
    ##### IIR Pole
    ##############

    @property
    def C0(self):
        return self._C0

    @C0.setter
    def C0(self, value):
        self._C0 = value

    @property
    def C1(self):
        return self._C1

    @C1.setter
    def C1(self, value):
        self._C1 = value

    @property
    def C2(self):
        return self._C2

    @C2.setter
    def C2(self, value):
        self._C2 = value

    @property
    def C3(self):
        return self._C3
    
    @C3.setter
    def C3(self, value):
        self._C3 = value

    def _update_iir(self):
        rho = self.P**15 / np.sin(self.theta)
        self._C0 = -1 * rho * self.P * np.sin(15 * self.theta)
        self._C1 = rho * np.sin(16 * self.theta)
        self._C2 = -1 * self.P**2 * self.C1
        self._C3 = rho * self.P * np.sin(17 * self.theta)

    ##############
    ##### IIR Incremental
    ##############

    @property
    def a1(self):
        return self._a1

    @a1.setter
    def a1(self, value):
        self._a1 = value

    @property
    def a2(self):
        return self._a2

    @a2.setter
    def a2(self, value):
        self._a2 = value

    def _update_as(self):
        self._a1 = 2 * self.P * np.cos(self.theta)
        self._a2 = self.P**2

    ##############
    ##### Complete Coefficients
    ##############

    def _update_coefficients(self):
        self._update_Xn()
        self._update_fir()
        self._update_iir()
        self._update_as()


    ###########################################
    ##### Specific coefficient setters
    ###########################################

    def set_zeroFIR(self, A = None, B = None):
        if A is not None:
            self.A = A
        if B is not None:
            self.B = B

    def set_Xn(self, X1 = None, X2 = None, X3 = None, X4 = None, X5 = None, X6 = None, X7 = None):
        X1 = X1 if X1 is not None else self.Xn[1]
        X2 = X2 if X2 is not None else self.Xn[2]
        X3 = X3 if X3 is not None else self.Xn[3]
        X4 = X4 if X4 is not None else self.Xn[4]
        X5 = X5 if X5 is not None else self.Xn[5]
        X6 = X6 if X6 is not None else self.Xn[6]
        X7 = X7 if X7 is not None else self.Xn[7]

        self._Xn = np.array([1, X1, X2, X3, X4, X5, X6, X7])

    def set_poleFIR(self, Dff = None, Dfg = None, Egg = None, Egf = None):
        if Dff is not None:
            self._Dff = Dff
        if Dfg is not None:
            self._Dfg = Dfg
        if Egg is not None:
            self._Egg = Egg
        if Egf is not None:
            self._Egf = Egf

    def set_poleIIR(self, C0=None, C1=None, C2=None, C3=None):
        if C0 is not None:
            self._C0 = C0
        if C1 is not None:
            self._C1 = C1
        if C2 is not None:
            self._C2 = C2
        if C3 is not None:
            self._C3 = C3

    def set_incremental(self, a1 = None, a2 = None):
        if a1 is not None:
            self._a1 = a1
        if a2 is not None:
            self._a2 = a2

    ###########################################
    ##### Implulse Response Filters
    ########################################### 

    def run_zeroFIR(self):
        pass

    def run_poleFIR(self):
        pass

    def run_poleIIR(self):
        pass

    def run_incremental(self):
        pass

    def run_FIR(self):
        self.run_zeroFIR()
        self.run_poleFIR()
    
    def run_IIR(self):
        self.run_FIR()
        self.run_poleIIR()

    def run_Biquad(self):
        self.run_IIR()
        # self.run_incremental()

    ###########################################
    ##### Print Coefficients
    ###########################################
    def printParams(self):
        print(f"A : {self.A}\nB : {self.B}\nP : {self.P}\nTheta : {self.theta}")

    def print_coeffs(self):
        print(f"X1 : {self.Xn[1]}\nX2 : {self.Xn[2]}\nX3 : {self.Xn[3]}\nX4 : {self.Xn[4]}\nX5 : {self.Xn[5]}\nX6 : {self.Xn[6]}\nX7 : {self.Xn[7]}\n")

        print(f"\nDff : {self.Dff}\nEgg : {self.Egg}\nDfg : {self.Dfg}\nEgf : {self.Egf}\n")

        print(f"\nC0 : {self.C0}\nC1 : {self.C1}\nC2 : {self.C2}\nC3 : {self.C3}\n")

        print(f"\na1 : {self.a1}\na2 : {self.a2}\n")

    ###########################################
    ##### Calculators
    ###########################################

    def quantise_coeffs(self):
        self.A = self.calc_q_format(self.A, 4, 14)
        self.B = self.calc_q_format(self.B, 4, 14)

        self.Xn = self.calc_q_format(self.Xn, 4, 14)

        self.Dff = self.calc_q_format(self.Dff, 4, 14)
        self.Dfg = self.calc_q_format(self.Dfg, 4, 14)
        self.Egg = self.calc_q_format(self.Egg, 4, 14)
        self.Egf = self.calc_q_format(self.Egf, 4, 14)

        self.C0 = self.calc_q_format(self.C0, 4, 14)
        self.C1 = self.calc_q_format(self.C1, 4, 14)
        self.C2 = self.calc_q_format(self.C2, 4, 14)
        self.C3 = self.calc_q_format(self.C3, 4, 14)

        self.a1 = self.calc_q_format(self.a1, 4, 14)
        self.a2 = self.calc_q_format(self.a2, 4, 14)

    def calc_chebyshev(self, num):
        return np.sin((num + 1) * self.theta) / np.sin(self.theta)
    
    def calc_18_bit(self, value):
        return int(np.floor(value * 16384))
    
    ##############
    ##### n-bit overflow, i.e. set bit width
    ##############

    def calc_q_format(self, value, m, n):
        min_val = -2**(m - 1)
        max_val = 2**(m - 1) - (1 / 2**n)
        scale_factor = 2**n

        scaled_value = np.floor(value * scale_factor)
        
        range_width = 2**(m + n)
        wrapped_value = ((scaled_value - min_val * scale_factor) % range_width) + min_val * scale_factor
        
        q_value = wrapped_value / scale_factor
        
        return q_value


    def calc_n_bit(self, value, n):
        min_val = -2**(n-1)
        max_val = 2**(n-1)
        
        range_width = max_val - min_val
        
        wrapped_value = ((value - min_val) % range_width) + min_val
        
        return wrapped_value

    ## Q4.14, what the daq reads/writes coefficients as. Not needed for the daq but required for daq->sim stuff
    def calc_4_bit(self, value, scale_factor=16384):
        scaled_value = np.floor(value * scale_factor)

        wrapped_scaled_value = ((scaled_value + (8 * scale_factor)) % (16 * scale_factor)) - (8 * scale_factor)
        fixed_point_value = wrapped_scaled_value / scale_factor
        
        return fixed_point_value

    ############################
    ##Extracts
    ############################

    def extract_raw(self):
        pass

    def extract_biquad(self):
        pass

if __name__ == '__main__':
    print(type(Biquad))

    biquad = Biquad(0.5,0.5,0.5,0.5)

    value = 4.58743952837958279378
    value = (2**14+1.6)/2**14

    print(biquad.calc_4_bit(value))
    print(biquad.calc_4_bit(value) - value)