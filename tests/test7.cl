class Main inherits IO {    

    step(p : AUTO_TYPE) : AUTO_TYPE { p.translate(1, 1) };

    test() : AUTO_TYPE {
        let p : AUTO_TYPE <- new Point in step(p)
    };
       
};