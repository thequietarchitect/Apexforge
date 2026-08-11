"""P11.7J canonical module-admission smoke test."""
from dataclasses import FrozenInstanceError

def req(c,m):
    if not c: raise AssertionError(m)

def err(t,f,m):
    try: f()
    except t: return
    raise AssertionError(m)

def main():
    from quad_vector.model import QuadVectorLane, QuadVectorResourceBudget
    from quad_vector.module import QuadVectorModuleKind
    from quad_vector.authoring.adapter import QuadVectorAuthoredModule, QuadVectorAuthoringSource, QuadVectorModuleDeclaration, adapt_quad_vector_module_declaration
    from quad_vector.admission import QuadVectorModuleAdmission, admit_quad_vector_modules

    budget=QuadVectorResourceBudget(max_modules=4,max_contributions=16,max_iterations=32)
    def make(source,author,cid,version,kind,deps=()):
        return adapt_quad_vector_module_declaration(QuadVectorModuleDeclaration(source=source,author_identity=author,canonical_id=cid,version=version,kind=kind,accepted_inputs=("quad.input",),produced_outputs=(cid+".out",),eligible_vectors=(QuadVectorLane.POSITIVE_X,),dependencies=deps,determinism_contract="pure-deterministic",authority_requirements=("quad.vector.read",),resource_budget=budget,implementation_reference="python:"+cid))
    base=make(QuadVectorAuthoringSource.HUMAN,"author:base","quad.module:BaseVelocity","1.0",QuadVectorModuleKind.FUNCTION)
    advisory=make(QuadVectorAuthoringSource.ADVISORY,"advisor:proposal","quad.module:AdaptiveWeight","0.1",QuadVectorModuleKind.WEIGHTING_RULE,("quad.module:BaseVelocity",))
    authored=(advisory,base)
    admission=admit_quad_vector_modules(authored,budget=budget)

    req(type(admission) is QuadVectorModuleAdmission,"non-canonical admission snapshot")
    req(admission.authored_modules==authored and admission.authored_modules[0] is advisory and admission.authored_modules[1] is base,"authored order/identity changed")
    req(admission.registry.specs==(advisory.spec,base.spec) and admission.registry.specs[0] is advisory.spec and admission.registry.specs[1] is base.spec,"registry spec order/identity changed")
    req(admission.authored_modules[0].source is QuadVectorAuthoringSource.ADVISORY and admission.authored_modules[0].author_identity=="advisor:proposal","advisory provenance changed")
    req(type(admission.authored_modules[0]) is QuadVectorAuthoredModule,"authored-module type changed")

    duplicate=make(QuadVectorAuthoringSource.TOOL,"tool:duplicate","quad.module:BaseVelocity","2.0",QuadVectorModuleKind.FUNCTION)
    err(ValueError,lambda:admit_quad_vector_modules((base,duplicate),budget=budget),"identity collision bypassed")
    missing=make(QuadVectorAuthoringSource.TOOL,"tool:missing","quad.module:MissingUser","1.0",QuadVectorModuleKind.FUNCTION,("quad.module:Absent",))
    err(ValueError,lambda:admit_quad_vector_modules((missing,),budget=budget),"unresolved dependency bypassed")
    small=QuadVectorResourceBudget(max_modules=1,max_contributions=16,max_iterations=32)
    err(ValueError,lambda:admit_quad_vector_modules((base,advisory),budget=small),"module budget bypassed")
    err(TypeError,lambda:admit_quad_vector_modules((object(),),budget=budget),"non-authored value accepted")
    err(TypeError,lambda:admit_quad_vector_modules([base],budget=budget),"non-tuple collection accepted")
    err(FrozenInstanceError,lambda:setattr(admission,"authored_modules",(base,)),"admission mutable")
    req(not any(hasattr(admission,n) for n in ("bind","execute","run","load","import_module","codex")),"admission gained runtime/loader/Codex privilege")

    print("Canonical authored-module admission order preservation: PASS")
    print("Author/source provenance preservation through admission: PASS")
    print("Canonical registry spec identity preservation: PASS")
    print("Registry identity/dependency validation reuse: PASS")
    print("Registry module-budget enforcement through admission: PASS")
    print("Exact authored-module admission boundary: PASS")
    print("Immutable admission snapshot boundary: PASS")
    print("P11.7J binding/execution/loader/Codex privilege exclusion: PASS")

if __name__=="__main__":
    main()
