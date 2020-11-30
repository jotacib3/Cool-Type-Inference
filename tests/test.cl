class Main inherits IO {
    main() : SELF_TYPE {
        let x : AUTO_TYPE <- 3 + 2 in
            case x of
                y : Int => out_string("Ok");
            esac
    };    
};