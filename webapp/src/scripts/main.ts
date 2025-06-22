import { renderMarkdown } from "./markdown";

import * as utils from "./utils";
import { TEXTS } from "./lang";
import GradientContainer from "../components/containers/GradientContainer.astro";
import Card from "../components/Card.astro";

window as any;

const WS_BASE_URL = "ws://localhost:8000/ws"
const ALERTS = false; // Set to true to enable alerts

const phaseProgress = document.getElementById('phase-progressbar') as HTMLDivElement;

const searchButton = document.getElementById('search-button') as HTMLButtonElement;
const urlTextbox = document.getElementById('url-textbox') as HTMLInputElement;

const mainContainer = document.getElementById('main-container') as HTMLDivElement;

const tabList = document.getElementById('tab-list') as HTMLUListElement;
const tabListForegroundButton = tabList.querySelector('.foreground-button') as HTMLButtonElement;
const summaryContainer = document.getElementById('summary-container') as HTMLDivElement;
const summaryMarkdown = document.getElementById('summary-markdown') as HTMLDivElement;
const expandButton = document.getElementById('expand-button') as HTMLButtonElement;

const conclusionCard = document.getElementById('conclusion-card') as HTMLDivElement;
const conclusionMarkdown = document.getElementById('conclusion-markdown') as HTMLDivElement;

const resultsSection = document.getElementById('results-section') as HTMLDivElement;
const verifiedProgress = document.getElementById('verified-progressbar') as HTMLDivElement;
const unverifiedProgress = document.getElementById('unverified-progressbar') as HTMLDivElement;
const neutralProgress = document.getElementById('neutral-progressbar') as HTMLDivElement;
const annotationPlaintext = document.getElementById('annotation-plaintext') as HTMLDivElement;

const domainBadges = document.getElementById('domain-badges') as HTMLDivElement;
const ipBadge = document.getElementById('ip-badge') as HTMLDivElement;
const ipBadgeText = document.getElementById('ip-badge-text') as HTMLDivElement;
const locationBadge = document.getElementById('location-badge') as HTMLDivElement;
const locationBadgeText = document.getElementById('location-badge-text') as HTMLDivElement;
const domainBadge = document.getElementById('domain-badge') as HTMLDivElement;
const domainBadgeText = document.getElementById('domain-badge-text') as HTMLDivElement;
const reputationBadge = document.getElementById('reputation-badge') as HTMLDivElement;

const articleBadges = document.getElementById('article-badges') as HTMLDivElement;
const noauthorBadge = document.getElementById('noauthor-badge') as HTMLDivElement;
const nosourcesBadge = document.getElementById('nosources-badge') as HTMLDivElement;

const extraBadges = document.getElementById('extra-badges') as HTMLDivElement;
const recentBadge = document.getElementById('recent-badge') as HTMLDivElement;
const grammarBadge = document.getElementById('grammar-badge') as HTMLDivElement;

const sourcesContainer = document.getElementById('sources-container') as HTMLDivElement;
const sourcesContainerTitle = document.getElementById('sources-container-title') as HTMLHeadingElement;
const sourcesContainerList = document.getElementById('sources-container-list') as HTMLUListElement;

const toUnhide = [
    phaseProgress,
    mainContainer
]

const toLoading = [ // Set to loading
    phaseProgress,
    summaryContainer,
    conclusionMarkdown,
    resultsSection,
    domainBadges,
    articleBadges,
    extraBadges,
    sourcesContainer,
]

const toBlur = [
    summaryContainer,
    conclusionMarkdown,
    resultsSection,
    domainBadges,
    articleBadges,
    extraBadges,
    sourcesContainer,
]

// Send messages
function sendMessage(msg: any) {
    if (socket.readyState !== WebSocket.OPEN) {
        socket.addEventListener('open', () => {
            console.log("WebSocket is now open, sending message."); 
            socket.send(JSON.stringify(msg));
        });
    }
    else{
        console.log("WebSocket is already open, sending message."); 
        socket.send(JSON.stringify(msg));
    }
}

function run(){
    // Unhide all elements
    unhideAll();

    setProgressBarState(phaseProgress, TEXTS.stateProgressBar.connecting);

    // Send URL to the backedn
    const url: string = urlTextbox.value.trim();
    console.log("Sending URL to backend:", url);

    const msg = {
        url: url,
    }

    sendMessage(msg);
}

function connect() {
    if (socket && socket.readyState === WebSocket.OPEN) {
        console.log("WebSocket is already open.");
    }
    else {
        // Start websockets
        startWebsockets();
    }

    // Set this button to disabled
    searchButton.disabled = true;
    urlTextbox.disabled = true;

    // Wait for the connection to be established
    socket.addEventListener('open', run);
}

// Event listeners
searchButton.addEventListener('click', () => {
    // Previous checks
    const url: string = urlTextbox.value.trim();

    if (!utils.isValidUrl(url) && url !== "mock") {
        showAlert("Please enter a valid URL.");

        urlTextbox.value = '';
        urlTextbox.focus();

        return;
    }

    connect();
});

tabList.addEventListener('click', async (event) => {
    // Get the tab value
    let value = tabList.getAttribute("value");
    let text = "";
    if (value === "0") {
        value = "1";

        text = tabList.getAttribute("data-text1") || "unset0";

        // Move the foreground button to the left
        tabListForegroundButton.style.left = "50%";
    }
    else{
        value = "0";

        text = tabList.getAttribute("data-text0") || "unset1";

        // Move the foreground button to the right
        tabListForegroundButton.style.left = "0%";
    }

    // Update the attribute
    const html = await renderMarkdown(text);
    summaryMarkdown.innerHTML = html;

    tabList.setAttribute("value", value);
});

expandButton.addEventListener('click', () => {
    summaryContainer.toggleAttribute("expanded");

    if (summaryContainer.hasAttribute("expanded")) {
        expandButton.value = TEXTS.summaryButton.close;
    } else {
        expandButton.value = TEXTS.summaryButton.open;
    }
});

// Websockets handling
let socket: WebSocket;

function startWebsockets() {
    console.log("Starting WebSocket connection...");
    
    socket = new WebSocket(WS_BASE_URL);
    (window as any).socket = socket; // For debugging purposes

    // Set up event listeners
    socket.addEventListener('message', onWebsocketMessage);
    socket.addEventListener('open', onWebsocketOpen);
    socket.addEventListener('error', onWebsocketError);
    socket.addEventListener('close', onWebsocketClose);
}
function onWebsocketMessage(event: MessageEvent) {
    console.log("WebSocket message received.");

    handleMessage(event.data)
}

function onWebsocketOpen() {
    console.log("WebSocket connection established.");
}

function onWebsocketError(error: any) {
    // Enable button and stop loading
    finishAnalysis();

    // Report the error
    console.error("WebSocket error:", error);
    showAlert(`Failed to connect to ${error.currentTarget?.url}`);
}

function onWebsocketClose() {
    console.log("WebSocket connection closed.");
    showAlert(`Server disconnected.`);

    // Enable button and stop loading
    finishAnalysis();
}

// Global UI/UX handling
function showAlert(message: string) {
    if (ALERTS) {
        alert(message);
    }
}

function unhideAll() {
    // Set blur
    utils.setAttributeToSuffixes(
        toBlur,
        "blur",
        "-blur"
    );

    // Set loading
    utils.setAttributeToSuffixes(
        toLoading,
        "loading",
        "-blur-loading"
    );

    setTimeout(() => {
        // Unhide main container
        toUnhide.forEach((element) => {
            element.removeAttribute("hidden");
        });
    }, 100);

    // Set everything as default
    conclusionCard.hidden = true;

    // Show all badges
    ipBadge.hidden = false;
    domainBadge.hidden = false;
    locationBadge.hidden = false;
    reputationBadge.hidden = true;

    noauthorBadge.hidden = false;
    nosourcesBadge.hidden = false;

    recentBadge.hidden = false;
    grammarBadge.hidden = false;
}

function stopLoadingAll() {
    // Remove loading
    utils.removeAttributeFromSuffixes(
        toLoading,
        "loading",
        "-blur-loading",
    );
}

function finishAnalysis() {
    // Set the button to enabled
    searchButton.disabled = false;
    urlTextbox.disabled = false;

    // Stop loading all elements
    stopLoadingAll();
}

function unBlur(element: any) {
    // Remove blur and loading attributes
    utils.handleAttributeToSuffix(
        element,
        "blur",
        "-blur",
        false
    );
    utils.handleAttributeToSuffix(
        element,
        "loading",
        "-blur-loading",
        false
    );
}

// Component UI/UX handling
function setProgressBarValue(
    progressBar: HTMLDivElement,
    value: number,
) {
    // Set the width of the progress bar
    const progressBarFill = progressBar.querySelector('.progressbar-fill') as HTMLDivElement;
    progressBarFill.style.width = `${value * 100}%`;

    // Set the displayed percentage
    const percentage = value * 100;

    const percentageElement = progressBar.querySelector('.percentage') as HTMLDivElement;
    percentageElement.textContent = `${percentage.toFixed(0)}%`;
}

function setProgressBarState(
    progressBar: HTMLDivElement,
    state: string,
) {
    const stateElement = progressBar.querySelector('.state') as HTMLDivElement;
    stateElement.textContent = state;
}

// Phase handling
function handleMessage(data_raw: string) {
    let data: any;
    try {
        data = JSON.parse(data_raw);
    } catch (e) {
        console.error("Failed to parse message:", e);
        return;
    }

    console.log("Received data:", data);

    // Check for errors
    if (data.error || data.refusal || data.exception) {
        if (data.error) {
            console.error("Error received:", data.error);
            showAlert(`Error: ${data.error}`);
        }
        if (data.refusal) {
            console.error(data.refusal);
            showAlert(data.refusal);
        }
        if (data.exception) {
            console.error("Server error:", data.exception);
            showAlert(`Exception: ${data.exception}`);
        }

        finishAnalysis();
        return;
    }

    // Phase-agnostic handling
    const state: string = TEXTS.stateProgressBar[data.phase as keyof typeof TEXTS.stateProgressBar || "unknown"];
    setProgressBarState(phaseProgress, state);

    // Phase-specific handling
    let phase_n = 0;
    const phase_n_total = 11;

    switch (data.phase) {
        case "check_domain":
            phase_n = 1;

            // Set the domain badges
            ipBadgeText.textContent = data.ip;
            locationBadgeText.textContent = `${data.ip_country}, ${data.ip_region}`;
            domainBadgeText.textContent = data.domain;
            
            // Unblur section
            unBlur(domainBadges);

            break;
        case "download_article":
            phase_n = 2;
            break;
        case "parse_article":
            phase_n = 3;

            break;
        case "process_article":
            phase_n = 4;

            // Set summary markdown
            const summaryHtml = renderMarkdown(data.summary) as string;
            tabList.setAttribute("data-text0", summaryHtml);
            summaryMarkdown.innerHTML = summaryHtml;

            // Set article markdown
            const articleHtml = renderMarkdown(data.markdown) as string;
            tabList.setAttribute("data-text1", articleHtml);

            // Unblur section
            unBlur(summaryContainer);

            break;
        case "search":
            phase_n = 5;
            break;
        case "process_search":
            phase_n = 6;

            // Clear container
            sourcesContainerList.innerHTML = "";

            // Add different sources to the container
            data.search_results.forEach((result: any) => {
                // Search if the item already exists
                const item = document.getElementById(`source-${result.url}`);
                if (item) {
                    // Already exists, skip
                    return;
                }

                // Get number of children
                const childrenCount = sourcesContainerList.children.length + 1;

                // Create a new list item
                const listItem = document.createElement('a');
                listItem.id = `source-${result.url}`;
                listItem.className = 'url';
                listItem.href = result.url;
                listItem.title = result.title;
                listItem.target = '_blank';

                listItem.innerHTML = (`
                    <h4>[${childrenCount}] ${result.title}</h4>
                    <p>${result.summary}</p>
                `);

                // Add the item to the container
                sourcesContainerList.appendChild(listItem);
            });

            // Update the sources count
            const sourcesCount = data.search_results.length;
            //sourcesContainerTitle.textContent = `${TEXTS.sourcesContainer.title} ${sourcesCount}`;

            // Unblur container (if blurry)
            if (!sourcesContainer.getAttribute("blur")) {
                unBlur(sourcesContainer);
            }
            break;
        case "rank_results":
            phase_n = 7;
            break;
        case "compare_results":
            phase_n = 8;
            break;
        case "draw_conclusion":
            phase_n = 9;

            console.log("verified percentage:", data.verified_percentage);
            console.log("unverified percentage:", data.unverified_percentage);
            console.log("unrelated percentage:", data.unrelated_percentage);

            const verified_percentage = Number(data.verified_percentage);
            const unverified_percentage = Number(data.unverified_percentage);
            const unrelated_percentage = Number(data.unrelated_percentage);

            const verified = data.verified;

            // Set the card text and annotation
            const conclusionCardLabel = conclusionCard.querySelector('.label') as HTMLDivElement;
            
            if (verified) {
                conclusionCardLabel.textContent = TEXTS.card.verified;
                conclusionCard.setAttribute("color", "green");

                const annotationText = TEXTS.anootation.verified.replace("{{percentage}}", verified_percentage.toFixed(0));
                annotationPlaintext.textContent = annotationText;
            }
            else{
                conclusionCardLabel.textContent = TEXTS.card.unverified;
                conclusionCard.setAttribute("color", "red");

                const annotationText = TEXTS.anootation.unverified.replace("{{percentage}}", (unverified_percentage + unrelated_percentage).toFixed(0));
                annotationPlaintext.textContent = annotationText;
            }

            // Set the conclusion markdown
            const conclusionHtml = renderMarkdown(data.conclusion) as string;
            const processedconclusionHtml = conclusionHtml.replace(/(\[.*\]\s)/g, "");
            conclusionMarkdown.innerHTML = processedconclusionHtml;

            // Set the results progress bars
            setProgressBarValue(verifiedProgress, data.verified_percentage);
            setProgressBarValue(unverifiedProgress, data.unverified_percentage);
            setProgressBarValue(neutralProgress, data.unrelated_percentage);

            // Show card
            conclusionCard.hidden = false;

            // Unblur sections
            unBlur(conclusionMarkdown);
            unBlur(resultsSection)

            break;
        case "last_checks":
            phase_n = 10;

            // Set the domain badges
            if (data.has_bad_reputation) {
                reputationBadge.hidden = false;
            }

            // Set the article badges
            if (data.noauthor) {
                noauthorBadge.hidden = false;
            }

            if (data.nosource) {
                nosourcesBadge.hidden = false;
            }

            // Set the extra badges
            if (data.recent) {
                recentBadge.hidden = false;
            }
            if (data.grammar) {
                grammarBadge.hidden = false;
            }

            // Unblur sections
            unBlur(articleBadges);
            unBlur(extraBadges);

            break;
        case "finished":
            phase_n = 11;

            finishAnalysis();

            break;
        default:
            console.warn("Unknown phase:", data.phase);
    }

    console.log(`Phase ${phase_n}: ${data.phase} (${state})`);

    // Set the progress bar value
    const progressValue = phase_n / phase_n_total;
    setProgressBarValue(phaseProgress, progressValue);
}

// Debugging
//run();