class Main inherits IO {    

    f(a: AUTO_TYPE, b: AUTO_TYPE) : AUTO_TYPE {
        if (a=1) then 
            b 
        else
            g(a + 1, b/2)
        fi
    };

    g(a: AUTO_TYPE, b: AUTO_TYPE) : AUTO_TYPE {
        if (b=1) then
            a
        else
            f(a/2, b+1)
        fi
    };   
};