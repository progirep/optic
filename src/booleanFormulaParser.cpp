//========================================================================
// This file contains the parser for Boolean formulas
//
// It is a modification of code given by ??? on
// http://stackoverflow.com/questions/12598029/how-to-calculate-boolean-expression-in-spirit
//
// and licensed separately from the rest of the program under
// CC-BY-SA
// terms (including the modifications performed).

#include "booleanFormulaParser.hpp"

#include <boost/spirit/include/qi.hpp>
#include <boost/spirit/include/phoenix.hpp>
#include <boost/spirit/include/phoenix_operator.hpp>
#include <boost/variant/recursive_wrapper.hpp>
#include <boost/lexical_cast.hpp>

namespace qi    = boost::spirit::qi;
namespace phx   = boost::phoenix;

struct op_or  {};
struct op_and {};
struct op_not {};
struct op_xor {};
struct op_equiv {};
struct op_imp {};
struct op_xabs {};

typedef std::string var;
template <typename tag> struct binop;
template <typename tag> struct unop;

typedef boost::variant<var,
        boost::recursive_wrapper<unop <op_not> >,
        boost::recursive_wrapper<binop<op_and> >,
        boost::recursive_wrapper<binop<op_or> >,
        boost::recursive_wrapper<binop<op_xor> >,
        boost::recursive_wrapper<binop<op_equiv> >,
        boost::recursive_wrapper<binop<op_imp> >,
        boost::recursive_wrapper<binop<op_xabs> >
        > expr;

template <typename tag> struct binop
{
    explicit binop(const expr& l, const expr& r) : oper1(l), oper2(r) { }
    expr oper1, oper2;
};

template <typename tag> struct unop
{
    explicit unop(const expr& o) : oper1(o) { }
    expr oper1;
};

struct eval : boost::static_visitor<BF>
{
    const EncoderContext &context;
    const std::map<std::string,BF> &definedBFs;

    eval(EncoderContext const &_context, const std::map<std::string,BF> &_definedBFs) : context(_context), definedBFs(_definedBFs) {}

    //
    BF operator()(const var& v) const
    {
        // Constants?
        if (v=="T" || v=="t" || v=="true" || v=="True" || v=="TRUE" || v=="1")
            return context.getBFMgr().constantTrue();
        else if (v=="F" || v=="f" || v=="false" || v=="False" || v=="FALSE" || v=="0")
            return context.getBFMgr().constantFalse();

        // Defined BFs?
        auto it = definedBFs.find(v);
        if (it!=definedBFs.end()) return it->second;

        // Variables
        return context.getVariableBF(v);
    }

    BF operator()(const binop<op_and>& b) const
    {
        return recurse(b.oper1) & recurse(b.oper2);
    }
    BF operator()(const binop<op_or>& b) const
    {
        return recurse(b.oper1) | recurse(b.oper2);
    }
    BF operator()(const binop<op_xor>& b) const
    {
        return recurse(b.oper1) ^ recurse(b.oper2);
    }
    BF operator()(const binop<op_imp>& b) const
    {
        return (!recurse(b.oper1)) | recurse(b.oper2);
    }
    BF operator()(const binop<op_equiv>& b) const
    {
        return !(recurse(b.oper1) ^ recurse(b.oper2));
    }
    BF operator()(const binop<op_xabs>& b) const
    {
        return recurse(b.oper1).ExistAbstractSingleVar(recurse(b.oper2));
    }
    BF operator()(const unop<op_not>& u) const
    {
        return !recurse(u.oper1);
    }

    private:
    template<typename T>
        BF recurse(T const& v) const
        { return boost::apply_visitor(*this, v); }
};



template <typename It, typename Skipper = qi::space_type>
struct parser : qi::grammar<It, expr(), Skipper>
{
        parser() : parser::base_type(expr_)
        {
            using namespace qi;

            expr_  = exabs_.alias();

            exabs_ = (var_ >> "$" >> exabs_) [ _val = phx::construct<binop<op_xabs > >(_2, _1) ] | equiv_ [ _val = _1 ];
            equiv_ = (imp_ >> "<->" >> equiv_) [ _val = phx::construct<binop<op_equiv > >(_1, _2) ] | imp_ [ _val = _1 ];
            imp_ =   (or_  >> "->" >> imp_) [ _val = phx::construct<binop<op_imp > >(_1, _2) ] | or_   [ _val = _1 ];
            or_  =   (xor_ >> '|'  >> or_ ) [ _val = phx::construct<binop<op_or > >(_1, _2) ] | xor_   [ _val = _1 ];
            xor_ =   (and_ >> '^'  >> xor_ ) [ _val = phx::construct<binop<op_xor > >(_1, _2) ] | and_   [ _val = _1 ];
            and_ =   (not_ >> '&' >> and_)  [ _val = phx::construct<binop<op_and> >(_1, _2) ] | not_   [ _val = _1 ];
            not_ =   ('!' > simple       )  [ _val = phx::construct<unop <op_not> >(_1)     ] | simple [ _val = _1 ];

            simple = (('(' > expr_ > ')') | var_);
            var_ = qi::lexeme[ +qi::char_("a-zA-Z_0-9") ];

            BOOST_SPIRIT_DEBUG_NODE(expr_);
            BOOST_SPIRIT_DEBUG_NODE(exabs_);
            BOOST_SPIRIT_DEBUG_NODE(imp_);
            BOOST_SPIRIT_DEBUG_NODE(or_);
            BOOST_SPIRIT_DEBUG_NODE(xor_);
            BOOST_SPIRIT_DEBUG_NODE(and_);
            BOOST_SPIRIT_DEBUG_NODE(not_);
            BOOST_SPIRIT_DEBUG_NODE(simple);
            BOOST_SPIRIT_DEBUG_NODE(var_);
        }

        private:
        qi::rule<It, var() , Skipper> var_;
        qi::rule<It, expr(), Skipper> not_, and_, xor_, or_, imp_, equiv_, exabs_, simple, expr_;
};



BF parseBooleanFormula(std::string const &formula, EncoderContext const &context,const std::map<std::string,BF> &definedBFs) {

    typedef std::string::const_iterator It;
    It f(formula.begin()), l(formula.end());
    parser<It> p;
    BF resultingBF;

    try
    {
        expr result;
        bool ok = qi::phrase_parse(f,l,p,qi::space,result);

        if (!ok)
            std::cerr << "invalid input\n";
        else {
            resultingBF = boost::apply_visitor(eval(context,definedBFs), result);
        }

    } catch (const qi::expectation_failure<It>& e)
    {
        std::ostringstream os;
        os << "Excepted expression part: "+std::string(e.first, e.last);
        throw os.str();
    }

    if (f!=l) throw "Unparsed string parts: '" + std::string(f,l) + "'";

    return resultingBF;
}
