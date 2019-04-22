#include <Engine/IEngine.h>
#include <Common/msgq.h>


namespace StarQuant
{

// mutex IEngine::sendlock_;
// std::unique_ptr<CMsgq> IEngine::msgq_send_;
IEngine::IEngine()
    :estate_(EState::DISCONNECTED)
    {
        init();
    }
IEngine::~IEngine(){
}
void IEngine::init(){

}
void IEngine::start(){

}
void IEngine::stop(){
    estate_ = EState::STOP;
}




}