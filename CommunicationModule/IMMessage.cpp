#include "StableHeaders.h"
#include "Foundation.h"

#include "IMMessage.h"


namespace TpQt4Communication
{
	Message::Message(std::string text, Contact* author) : text_(text), author_(author), time_stamp_(QTime::currentTime())
	{
	}

	std::string Message::GetText()
	{
		return text_;
	}

	Contact* Message::GetAuthor()
	{
		return author_;
	}

	QTime Message::GetTimeStamp()
	{
		return time_stamp_;
	}


} // end of namespace: TpQt4Communication
