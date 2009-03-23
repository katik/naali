// For conditions of distribution and use, see copyright notice in license.txt

#ifndef incl_Interfaces_ConsoleCommandServiceInterface_h
#define incl_Interfaces_ConsoleCommandServiceInterface_h

#include "ServiceInterface.h"

namespace Console
{
    //! A result from executing a console command.
    /*! A callback function for console command should return an instance.
    */
    struct CommandResult
    {
        //! Set to true if command was completed succesfully, false otherwise
        bool success_;
        //! Print out reason for failure (or success).
        std::string why_;
        //! True for delayed execution. For internal use, this doesn't need to be set normally
        bool delayed_;
    };
    //! Returns a succesful CommandResult
    __inline static CommandResult ResultSuccess(const std::string &why = std::string()) { CommandResult result = { true, why, false}; return result; }
    //! Returns a failure CommandResult
    __inline static CommandResult ResultFailure(const std::string &why = std::string()) { CommandResult result = { false, why, false}; return result; }
    //! Returns a failure CommandResult, with invalid parameters as the reason
    __inline static CommandResult ResultInvalidParameters() { CommandResult result = { false, "Invalid parameters.", false}; return result; }
    //! Returns a delayed CommandResult
    __inline static CommandResult ResultDelayed() { CommandResult result = { false, std::string(), true }; return result; }

    //! Interface for console command callback
    class CallbackInterface
    {
    public:
        CallbackInterface() {}
        virtual ~CallbackInterface() {}

        //! Calls the function
        virtual CommandResult operator()(const Core::StringVector &params) = 0;
    };
    typedef boost::shared_ptr<CallbackInterface> CallbackPtr;

    //! typedef for static callback
    typedef CommandResult (*StaticCallback)(const Core::StringVector&);

    //! functor for console command callback, member function callback
    template <typename T>
    class Callback : public CallbackInterface
    {
    public:
        typedef CommandResult (T::*CallbackFunction)(const Core::StringVector&);

        //! constructor taking object and member function pointer
        Callback(T *object, CallbackFunction function) : object_(object), function_(function) { }

        //! destructor
        virtual ~Callback() {}

        //! copy constructor
        Callback(const Callback &rhs)
        {
            this->object_ = rhs.object_;
            this->function_ = rhs.function_;
        }
        Callback &operator=(const Callback &rhs)
        {
            if (this != &rhs)
            {
                object_ = rhs.object_;
                function_ = rhs.function_;
            }
            return *this;
        }

        //! Calls the function
        virtual CommandResult operator()(const Core::StringVector &params)
        {
            return (*object_.*function_)(params);
        }       

    private:
        //! pointer to the object
        T *object_;
        //! pointer to the member function
        CallbackFunction function_;
    };

    //! functor for console command callback, for static function callback
    class StaticCallbackFunctor : public CallbackInterface
    {
    public:
        //! constructor taking static function pointer
        StaticCallbackFunctor(StaticCallback &function) : function_(function) { }

        //! destructor
        virtual ~StaticCallbackFunctor() {}

        //! copy constructor
        StaticCallbackFunctor(const StaticCallbackFunctor &rhs)
        {
            this->function_ = rhs.function_;
        }

        StaticCallbackFunctor &operator=(const StaticCallbackFunctor &rhs)
        {
            if (this != &rhs)
            {
                function_ = rhs.function_;
            }
            return *this;
        }

        //! Calls the function
        virtual CommandResult operator()(const Core::StringVector &params)
        {
            return (*function_)(params);
        }       

    private:
        //! pointer to function
        StaticCallback function_;
    };

    //! A console command
    struct Command
    {
        //! internal name for the command, case insensitive
        std::string name_;
        //! short description of the command
        std::string description_;
        //! callback for the command
        CallbackPtr callback_;
        //! is the handling of the command immediate, or delayed
        bool delayed_;
    };

    //! Creates a console command with member function callback
    /*!
        \param name name of the command
        \param description short description of the command
        \param C++ function callback. Use Console::Bind().
    */
    static Command CreateCommand(const std::string &name, const std::string &description, const CallbackPtr &callback, bool delayed = false)
    {
        Command command = { name, description, callback, delayed };
        return command;
    }

    //! Creates a console command with static function callback
    /*!
        \param name name of the command
        \param description short description of the command
        \param C++ function callback. Use Console::Bind().
    */
    static Command CreateCommand(const std::string &name, const std::string &description, StaticCallback &static_callback, bool delayed = false)
    {
        CallbackPtr callback(new StaticCallbackFunctor(static_callback));
        Command command = { name, description, callback, delayed };
        return command;
    }

    //! Bind a member function to a command callback
    template <typename T>
    static CallbackPtr Bind(T *object, typename Callback<T>::CallbackFunction function)
    {
        return CallbackPtr(new Callback<T>(object, function));
    }

    //! Interface for console command service.
    /*! One can register and execute registered console commands by using this service.
        Commands can be parsed and executed from a commandline string, or executed directly.

        One can register new commands with RegisterCommand() - functions.
        Each command has a name and a small description. Command names are case-insensitive.
        Each command is associated with C++ callback function, the function can be a static
        function or a member function, but it should have the signature:

            CommandResult Foo(const Core::StringVector& parameters)

        where parameters contains parameters supplied with the command.

        For threadsafe execution of the callbacks, use QueueCommand() when supplying
        commandlines from the user (only for Console-type of classes), and register commands
        with delayed execution and use Poll() to execute the commands in the caller's
        thread context.
        F.ex.

            RegisterCommand("MyCommand", "My great command", &MyClass::MyFunction, true); // register command for delayed execution

            then in MyClass' update function, in thread context other than the main thread
            void MyClass::Update()
            {
                ConsoleCommandService->Poll("MyCommand"); // If MyCommand was queued previously, it now gets executed.
                // ...
            }

        \note All functions should be threadsafe. Commands should be registered in PostInitialize or later.
    */
    class ConsoleCommandServiceInterface : public Foundation::ServiceInterface
    {
    public:
        //! default constructor
        ConsoleCommandServiceInterface() {}

        //! destructor
        virtual ~ConsoleCommandServiceInterface() {}

        //! add time
        virtual void Update() {}

        //! Add a command to the debug console
        virtual void RegisterCommand(const Command &command) = 0;

        //! Register a command to the debug console
        /*! For binding a member function.
            To bind a member function to the command, use Console::Bind()

            \param name name of the command
            \param description short description of the command
            \param callback function object that gets called when command is executed
            \param delayed If true, handle the command in delayed, threadsafe manner
        */
        virtual void RegisterCommand(const std::string &name, const std::string &description, const CallbackPtr &callback, bool delayed = false) = 0;

        //! Register a command to the debug console
        /*! For binding a static function

            \param name name of the command
            \param description short description of the command
            \param callback function object that gets called when command is executed
            \param delayed If true, handle the command in delayed, threadsafe manner
        */
        virtual void RegisterCommand(const std::string &name, const std::string &description, StaticCallback &static_callback, bool delayed = false) = 0;

        //! Unregister console command with the specified name
        virtual void UnregisterCommand(const std::string &name) = 0;

        //! Queue console command. The command will be called in the console's thread
        /*!
            \param commandline string that contains the command and any parameters
        */
        virtual void QueueCommand(const std::string &commandline) = 0;

        //! Poll to see if command has been queued and executes it immediately, in the caller's thread context.
        /*! For each possible command, this needs to be called exactly once.

            \param command name of the command to poll for.
            \return Result of executing the command, 
        */
        virtual boost::optional<CommandResult> Poll(const std::string &command) = 0;

        //! Parse and execute command line. The command is called in the caller's thread.
        virtual CommandResult ExecuteCommand(const std::string &commandline) = 0;

        //! Execute command
        /*!
            \param name Name of the command to execute
            \param params Parameters to pass to the command
        */
        virtual CommandResult ExecuteCommand(const std::string &name, const Core::StringVector &params) = 0;
    };

    typedef ConsoleCommandServiceInterface CommandService;
    typedef boost::shared_ptr<CommandService> CommandManagerPtr;
}

#endif

