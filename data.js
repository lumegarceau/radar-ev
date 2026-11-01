var AFF={
"1XBET":"https://aff.tipsterpage.com/v/22626",
"888 Sports":"https://bdeal.io/888Sport/158811/1",
"Bet365":"https://bdeal.io/Bet365/162245/1",
"Betfair":"https://bdeal.io/Betfair/159010/2",
"Betsson":"https://bdeal.io/Betsson/158599/1",
"Betway":"https://bdeal.io/Betway/158233/1",
"Bwin":"https://link2play.com/24375/Superaumentos",
"Gran Casino Madrid":"https://bdeal.io/CGranMadrid/158231/1",
"Casino Marbella":"https://bdeal.io/CasinoMarbella/158810/1",
"Codere":"https://bdeal.io/Codere/158232/1",
"Daznbet":"https://bdeal.io/daznbet/162598/1",
"Goldenbull":"https://bdeal.io/goldenbull/159940/1",
"Interwetten":"https://bdeal.io/Interwetten/159941/1",
"Kirolbet":"https://bdeal.io/Kirolbet/158600/1",
"Luckia":"https://bdeal.io/Luckia/158258/1",
"Marcaapuestas":"https://bdeal.io/marcaapuestas/158240/1",
"Paf":"https://bdeal.io/PAF/158294/1",
"Retabet":"https://aff.tipsterpage.com/v/22616",
"Speedybet":"https://bdeal.io/speedybet/158237/1",
"Sportium":"https://bdeal.io/Sportium/158239/1",
"Versus":"https://bdeal.io/Versus/158238/1",
"William Hill":"https://bdeal.io/WilliamHill/158234/1",
"Winamax":"https://bdeal.io/Winamax/158235/1",
"Yosports":"https://bdeal.io/YoSports/158236/1"
};
function nk(s){return String(s||"").toLowerCase().replace(/[^a-z0-9]/g,"")}
var AFFN={};
Object.keys(AFF).forEach(function(k){AFFN[nk(k)]=AFF[k]});
function link(b){return AFFN[nk(b)]||"#"}
var ORDER=["España","Inglaterra","Italia","Francia","Alemania","Países Bajos","Portugal"];
var LIGAS=["LaLiga","Segunda División","Liga F","Premier League","Serie A","Ligue 1","Bundesliga","Eredivisie","Primeira Liga"];
var FLAG={"España":"🇪🇸","Inglaterra":"🇬🇧","Italia":"🇮🇹","Francia":"🇫🇷","Alemania":"🇩🇪","Países Bajos":"🇳🇱","Portugal":"🇵🇹"};
var TABS=[["radar","Radar"],["errores","Errores de cuota"],["bookies","Bookies"],["resultados","Resultados"]];
var DEMO=[
{pais:"España",liga:"LaLiga",local:"Real Madrid",visitante:"Valencia",hora:"21:00",suceso:"Real Madrid +4,5 córners",l20:"16/20",cond:"9/10",condTxt:"local",rival:"12/20",prob:.78,cuotas:[{b:"Bet365",c:1.80},{b:"Winamax",c:1.73},{b:"Codere",c:1.70},{b:"Betfair",c:1.65}]},
{pais:"España",liga:"LaLiga",local:"Real Madrid",visitante:"Valencia",hora:"21:00",suceso:"Valencia +3,5 tarjetas",l20:"15/20",cond:"8/10",condTxt:"visitante",rival:"13/20",prob:.74,cuotas:[{b:"Winamax",c:2.30},{b:"Bet365",c:1.85}]},
{pais:"España",liga:"Segunda División",local:"Eibar",visitante:"Racing",hora:"18:30",suceso:"Más de 2,5 goles",l20:"15/20",cond:"7/10",condTxt:"local",rival:"11/20",prob:.71,cuotas:[{b:"Codere",c:1.62},{b:"Winamax",c:1.60}]},
{pais:"Inglaterra",liga:"Premier League",local:"Arsenal",visitante:"Brentford",hora:"17:30",suceso:"Arsenal +5,5 córners",l20:"15/20",cond:"8/10",condTxt:"local",rival:"10/20",prob:.72,cuotas:[{b:"Bet365",c:1.95},{b:"Winamax",c:1.88},{b:"Betfair",c:1.80}]},
{pais:"Italia",liga:"Serie A",local:"Inter",visitante:"Torino",hora:"20:45",suceso:"Inter +11,5 tiros",l20:"17/20",cond:"9/10",condTxt:"local",rival:"14/20",prob:.82,cuotas:[{b:"Winamax",c:1.50},{b:"Bet365",c:1.45}]},
{pais:"Alemania",liga:"Bundesliga",local:"Leverkusen",visitante:"Mainz",hora:"15:30",suceso:"Más de 22,5 faltas",l20:"14/20",cond:"7/10",condTxt:"local",rival:"12/20",prob:.70,cuotas:[{b:"Codere",c:1.75},{b:"Winamax",c:1.70}]}
];
