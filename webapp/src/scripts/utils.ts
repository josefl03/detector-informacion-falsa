export function isValidUrl(url: string): boolean {
    try {
        new URL(url);
        return true;
    } catch (e) {
        return false;
    }
}

export function handleAttributeToSuffix(
    element: HTMLDivElement,
    attribute: string,
    suffix: string,
    set: boolean
) {
    const id = element.id;
    const suffixElement = document.getElementById(id + suffix);
    if (suffixElement) {
        if (set) {
            suffixElement.setAttribute(attribute, "");
        } else {
            suffixElement.removeAttribute(attribute);
        }
    } else {
        console.warn(`Element with no ID found:`, element);
    }
}

export function setAttributeToSuffixes(
    elements: HTMLDivElement[],
    attribute: string,
    suffix: string
) {
    elements.forEach((element) => {
        handleAttributeToSuffix(element, attribute, suffix, true);
    });
}

export function removeAttributeFromSuffixes(
    elements: HTMLDivElement[],
    attribute: string,
    suffix: string
) {
    elements.forEach((element) => {
        handleAttributeToSuffix(element, attribute, suffix, false);
    });
}