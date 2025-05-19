#pragma once
#include <string>
#include <exception>
#include <WString.h>

class SetupError : public std::exception
{
protected:
    String mMessage;

public:
    SetupError(const char *msg) : mMessage(String(msg)) {}

    const char *what() const throw()
    {
        return mMessage.c_str();
    }
};