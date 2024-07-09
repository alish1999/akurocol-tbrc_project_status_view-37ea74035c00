class AkuroManager{
    constructor(){
        this.components = {};
        this.instances = {};
        this.counter = 0;
    }
    registerComponent(name, dependencies, instantiator){
        this.components[name] = instantiator;
    }
    instantiateInner(typ, elm_list, ignore_old){
        
               
        if(this.components[typ] === undefined){
            console.log("error al instanciar un componente, tipo no encontrado: "+typ)
        }

        if(elm_list === null || typeof elm_list == "undefined"){
            console.log("error al instanciar un componente")
        }
        
        let final_list = [];
        
        if (elm_list.length !== undefined){
            final_list = elm_list
        }else{
            final_list = [elm_list];
        }

        final_list.forEach((elm)=>{
            let mustInstantiate = true;
            if (!ignore_old){
                let old_key = elm.dataset.akuro_key;
                if (old_key!==null && old_key!==undefined){
                    console.log("componente ya instanciado");
                    mustInstantiate = false;
                }
            }
            if (mustInstantiate){
                this.counter++;
                this.instances[this.counter] = this.components[typ](elm);
                elm.dataset.akuro_key = this.counter;
            }
        })
    }
    
    instantiate(typ, elm_list){
        this.instantiateInner(typ, elm_list, false);
    }

    getElm(elm){
        return akuro.instances[elm.dataset.akuro_key];
    }
    
    reinstantiateChildren(elm){
        elm.querySelectorAll("[data-akuro-ct]").forEach((inner_elm)=>{
            try{
              this.instantiateInner(inner_elm.dataset.akuroCt, inner_elm, true);
            }catch(e){}
        });
    }
}

class AkuroInput{
    constructor(elm){
        this.elm = elm;
    }
    getValue(){
        return null;
    }
}

class LoadedElm{
    constructor(elm, load){
        this.elm = elm;
        this.load = load;
    }
    getValue(){
        return null;
    }
}

akuro = new AkuroManager();