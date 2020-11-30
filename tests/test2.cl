class Main inherits IO {

    fact(n : AUTO_TYPE): AUTO_TYPE {
        if (n<0) then 1 else n*fact(n-1) fi
    };

    ackermann(m : AUTO_TYPE, n: AUTO_TYPE) : AUTO_TYPE {
        if (m=0) then 
            n+1
        else
            if (n=0) then 
                ackermann(m-1, 1) 
            else
                ackermann(m-1, ackermann(m, n-1))
            fi
        fi
    };    
};