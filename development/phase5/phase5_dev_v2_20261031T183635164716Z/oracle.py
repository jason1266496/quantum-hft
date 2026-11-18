from fractions import Fraction as F
from itertools import product
# Fixed before compiler execution; independent original, unexpanded objective.
FIXED=(
 {'mu':F(2),'f':(F(1),F(-3,2),F(-1),F(1,2)),'A':F(5),'optimal_bits':('0010',),'optimum':F(-3,2)},
 {'mu':F(4),'f':(F(1),F(-7,2),F(-5),F(-11,2)),'A':F(16),'optimal_bits':('1000',),'optimum':F(-11,2)},
 {'mu':F(0),'f':(F(1),F(1,2),F(3),F(13,2)),'A':F(12),'optimal_bits':('0010',),'optimum':F(1,2)},
 {'mu':F(-1,2),'f':(F(1),F(1),F(4),F(8)),'A':F(15),'optimal_bits':('0001','0010'),'optimum':F(1)},
 {'mu':F(-1),'f':(F(1),F(3,2),F(5),F(19,2)),'A':F(18),'optimal_bits':('0001',),'optimum':F(1)},
)
def original(mu,x):
    return sum(x[i]*(-mu*i+abs(i-1)+F(1,2)*i*i) for i in range(4))+(1+sum(abs(-mu*i+abs(i-1)+F(1,2)*i*i) for i in range(4)))*(sum(x)-1)**2
