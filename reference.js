'use strict';
const https = require("https");
const querystring = require('querystring');
/*
APOLOGY:
50% of this mess is because I'm lazy and don't want to package a 
requests library up to Amazon, That should probably be fixed.
The other 50% is brittle regexes to parse the SOS website. That
SHOULD be fixed, but lord knows how.
-S, December 2017
*/
// Gather registration data from the response; most of it is in
// a not-table. This is *probably* the function you're here to edit.
const parseRegistered = (body) => {
    const registered = !!body.match(/Yes\, You Are Registered/);
    if (!registered) return { registered: false };
    const ret = { registered: !!body.match(/Yes\, You Are Registered/) };
    const rex = /districtCell">[\s\S]*?<b>(.*?): <\/b>[\s\S]*?districtCell">[\s\S]*?">(.*?)<\/span>/g
    do {
        var m = rex.exec(body);
        if (m) {
            ret[m[1].toLowerCase().replace(/\s/g, '_')] = m[2];
        }
    } while (m);
    return ret;
}
// Grabs the XSS validation tokens from the form.
const parseTokens = (body) => {
    return {
        '__EVENTVALIDATION': body.match(/id="__EVENTVALIDATION" value="(.*?)"/)[1],
        '__VIEWSTATE': body.match(/id="__VIEWSTATE" value="(.*?)"/)[1],
        '__VIEWSTATEGENERATOR': body.match(/id="__VIEWSTATEGENERATOR" value="(.*?)"/)[1],
        '__VIEWSTATEENCRYPTED': ''
    };
};
// Fetch the HTML form that we're automating
const fetchTokens = (callback) => {
    https.get('https://webapps.sos.state.mi.us/MVIC/', (res) => {
        res.setEncoding("utf8");
        let body = "";
        res.on("data", data => {
            body += data;
        });
        res.on("end", () => callback(body));
    })
};
const fetchRegistered = (personData, tokens, callback) => {
    // Don't ask me, the SOS wants the data delivered this way.
    const formData = Object.assign({}, {
        'ctl00$ContentPlaceHolder1$vsFname': personData.firstName, 
        'ctl00$ContentPlaceHolder1$vsLname': personData.lastName, 
        'ctl00$ContentPlaceHolder1$vsMOB2': personData.birthMonth,
        'ctl00$ContentPlaceHolder1$vsMOB1': personData.birthMonth,
        'ctl00$ContentPlaceHolder1$vsYOB2': personData.birthYear, 
        'ctl00$ContentPlaceHolder1$vsZip': personData.zip, 
        'ctl00$ContentPlaceHolder1$btnSearchByName': 'Search',
    }, tokens);
    const postData = querystring.stringify(formData);
    
    // Below: no business logic, just the horror of https instead 
    // of requests. Sorry.
    const options = {
        hostname: 'webapps.sos.state.mi.us',
        path: '/MVIC/',
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Content-Length': Buffer.byteLength(postData)
        }
    };
    const req = https.request(options, (res) => {
        res.setEncoding("utf8");
        let body = "";
        res.on("data", data => {
            body += data;
        });
        res.on("end", () => callback(body));
    });
    req.on('error', (e) => {
      console.error(`problem with request: ${e.message}`);
    });
    req.write(postData);
    req.end();
}
// This is where all the lego pieces are assembled in a miserable 
// block of callbacks. Callbacks instead of promises because https 
// instead of requests.
const buildRequest = (personData, callback) => {
    fetchTokens(body => {
        const tokens = parseTokens(body)
        fetchRegistered(personData, tokens, body => {
            callback(parseRegistered(body));
        });
    });
}
exports.handler = (event, context, callback) => {
    const respond = (ret) => {
        callback(null, {
            statusCode: '200',
            body: JSON.stringify(ret),
            headers: {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
        });
    };
    buildRequest(event.queryStringParameters, respond);
};
